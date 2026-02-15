from pymongo import MongoClient
from bot import MONGO_URI, LOGGER

def start():
    if not MONGO_URI:
        LOGGER.error("MONGO_URI is missing. Exiting now.")
        exit(1)
    try:
        client = MongoClient(MONGO_URI)
        db = client["musicbot"]
        LOGGER.info("Connected to MongoDB successfully.")
        return db
    except Exception as e:
        LOGGER.error(f"Failed to connect to MongoDB: {e}")
        exit(1)

DB = start()
