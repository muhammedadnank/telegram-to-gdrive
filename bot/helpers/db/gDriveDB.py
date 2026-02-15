import json
from oauth2client.client import OAuth2Credentials
from bot.helpers.db import DB

collection = DB["gDrive"]


def _set(chat_id, credential_string):
    # Safely serialize using oauth2client's built-in JSON method
    try:
        creds_json = credential_string.to_json()
        collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"credential_string": creds_json}},
            upsert=True
        )
    except Exception as e:
        print(f"MongoDB gDriveDB set error: {e}")


def search(chat_id):
    # Safely deserialize using oauth2client's built-in from_json method
    try:
        result = collection.find_one({"chat_id": chat_id})
        if result:
            return OAuth2Credentials.from_json(result["credential_string"])
        return None
    except Exception as e:
        print(f"MongoDB gDriveDB search error: {e}")
        return None


def _clear(chat_id):
    try:
        collection.delete_one({"chat_id": chat_id})
    except Exception as e:
        print(f"MongoDB gDriveDB clear error: {e}")
