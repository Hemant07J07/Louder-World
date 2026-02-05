import hashlib
from datetime import datetime
from dateutil import parser as dateparser

def make_checksum(*args):
    """
    Compute sha256 checksum from normalized strings
    """
    s = "|".join((str(a or "").strip() for a in args))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def parse_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return dateparser.parse(dt_str)
    except Exception:
        return None
    
def now_iso():
    return datetime.utcnow().isoformat() + "Z"