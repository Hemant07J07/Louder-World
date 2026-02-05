from django.conf import settings
from pymongo import MongoClient
from bson.objectid import ObjectId

client = MongoClient(
    settings.MONGO_URI,
    serverSelectionTimeoutMS=2000,
    connectTimeoutMS=2000,
    socketTimeoutMS=2000,
)
db = client[settings.MONGO_DB]
events_coll = db["events"]
subscriptions_coll = db["subscriptions"]

# Help to convert mongo desc into JSON-serializable dict
def serialize_event(doc):
    if not doc:
        return None
    d = dict(doc)
    # convert ObjectID to string
    d["id"] = str(d.pop("_id"))
    return d