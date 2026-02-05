from pymongo import MongoClient
import os

MONGO_URI  = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.environ.get("MONGO_DB", "events_db")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
events_coll = db["events"]