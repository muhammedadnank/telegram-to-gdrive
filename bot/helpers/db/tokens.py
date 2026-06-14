from bot.helpers.db import DB

_col = DB["page_tokens"]


def get(folder_id: str):
    """Return the stored page token for a folder, or None."""
    try:
        doc = _col.find_one({"_id": folder_id})
        return doc["page_token"] if doc else None
    except Exception as e:
        print(f"tokens.get error: {e}")
        return None


def set(folder_id: str, token: str):
    """Persist the latest page token for a folder."""
    try:
        _col.update_one(
            {"_id": folder_id},
            {"$set": {"page_token": token}},
            upsert=True,
        )
    except Exception as e:
        print(f"tokens.set error: {e}")


def delete(folder_id: str):
    try:
        _col.delete_one({"_id": folder_id})
    except Exception as e:
        print(f"tokens.delete error: {e}")
