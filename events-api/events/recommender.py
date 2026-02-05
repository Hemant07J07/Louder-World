import os
import json
import numpy as np
from sentence_transformers import SentenceTransformer
from .mongo import events_coll, serialize_event

try:
    import faiss  # type: ignore
    _HAVE_FAISS = True
except Exception:
    faiss = None
    _HAVE_FAISS = False

# Config
MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")  # small, fast model
EMBED_DIM = 384  # all-MiniLM-L6-v2 -> 384 dim
INDEX_DIR = os.environ.get("FAISS_INDEX_DIR", os.path.join(os.getcwd(), "faiss_index"))
INDEX_FILE = os.path.join(INDEX_DIR, "events.index")
EMBEDDINGS_FILE = os.path.join(INDEX_DIR, "embeddings.npy")
MAPPING_FILE = os.path.join(INDEX_DIR, "id_mapping.json")

# Lazy model load
_model = None
def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def embed_texts(texts):
    model = get_model()
    embeddings = model.encode(texts, show_progress_bar=False, convert_to_numpy=True, normalize_embeddings=True)
    return embeddings  # shape (n, d)

def build_index(rebuild=True, batch_size=256):
    """
    Build / rebuild FAISS index from all events in Mongo.
    Stores index file and mapping from rowid -> mongo_id
    """
    os.makedirs(INDEX_DIR, exist_ok=True)
    # collect events
    cursor = events_coll.find({"status": {"$ne": "inactive"}})  # only index active/new/updated or imported
    docs = []
    ids = []
    texts = []
    for d in cursor:
        # create a short textual representation for embedding
        title = d.get("title","") or ""
        desc = d.get("description","") or ""
        venue = d.get("venue","") or ""
        text = " | ".join([title, venue, desc])
        docs.append(d)
        ids.append(str(d["_id"]))
        texts.append(text)

    if len(texts) == 0:
        if _HAVE_FAISS:
            index = faiss.IndexFlatIP(EMBED_DIM)
            faiss.write_index(index, INDEX_FILE)
        else:
            np.save(EMBEDDINGS_FILE, np.zeros((0, EMBED_DIM), dtype="float32"))
        with open(MAPPING_FILE, "w") as f:
            json.dump({"ids": []}, f)
        return {"built": 0}

    # embed in batches to limit memory
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        emb = embed_texts(batch)
        embeddings.append(emb)
    embeddings = np.vstack(embeddings).astype("float32")

    # we will use normalized vectors and inner product for cosine similarity (vectors normalized above)
    if _HAVE_FAISS:
        index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        faiss.write_index(index, INDEX_FILE)
    else:
        np.save(EMBEDDINGS_FILE, embeddings)

    # write id mapping (row idx -> mongo id)
    with open(MAPPING_FILE, "w") as f:
        json.dump({"ids": ids}, f)

    return {"built": len(ids)}

def load_index():
    if not os.path.exists(MAPPING_FILE):
        return None, None
    with open(MAPPING_FILE, "r") as f:
        mapping = json.load(f)
    ids = mapping.get("ids", [])

    if _HAVE_FAISS and os.path.exists(INDEX_FILE):
        index = faiss.read_index(INDEX_FILE)
        return index, ids

    if os.path.exists(EMBEDDINGS_FILE):
        embeddings = np.load(EMBEDDINGS_FILE)
        return embeddings, ids

    return None, ids

def query_by_vector(vec, k=8):
    """
    vec: numpy array shape (d,) or (1,d), must be normalized if index built with normalized vectors
    returns list of tuples (mongo_id, score)
    """
    index_or_embeddings, ids = load_index()
    if index_or_embeddings is None:
        return []

    xq = np.array(vec, dtype="float32").reshape(1, -1)

    if _HAVE_FAISS and hasattr(index_or_embeddings, "search"):
        D, I = index_or_embeddings.search(xq, k)
        results = []
        for score, idx in zip(D[0], I[0]):
            if idx < 0 or idx >= len(ids):
                continue
            results.append((ids[idx], float(score)))
        return results

    embeddings = np.array(index_or_embeddings, dtype="float32")
    if embeddings.size == 0:
        return []
    # embeddings are already normalized; use dot-product for cosine similarity
    scores = (embeddings @ xq.reshape(-1)).astype("float32")
    topk = int(min(max(k, 1), scores.shape[0]))
    idxs = np.argpartition(-scores, topk - 1)[:topk]
    idxs = idxs[np.argsort(-scores[idxs])]
    results = []
    for idx in idxs.tolist():
        if idx < 0 or idx >= len(ids):
            continue
        results.append((ids[idx], float(scores[idx])))
    return results

def recommend_by_event(event_id, k=8):
    # find event in mongo
    doc = events_coll.find_one({"_id": __import__("bson").ObjectId(event_id)})
    if not doc:
        return []
    text = " | ".join([doc.get("title","") or "", doc.get("venue","") or "", doc.get("description","") or ""])
    emb = embed_texts([text])[0]
    return query_by_vector(emb, k=k)

def recommend_by_preferences(preferences_text, k=8):
    # preferences_text: string describing what user likes
    emb = embed_texts([preferences_text])[0]
    return query_by_vector(emb, k=k)

def fetch_events_with_scores(id_score_pairs):
    """
    Convert list of (mongo_id_str, score) into serialized event docs
    """
    res = []
    for mid, score in id_score_pairs:
        try:
            from bson.objectid import ObjectId
            doc = events_coll.find_one({"_id": ObjectId(mid)})
            if doc:
                d = serialize_event(doc)
                d["score"] = score
                res.append(d)
        except Exception:
            continue
    return res
