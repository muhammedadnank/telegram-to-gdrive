from bot.helpers.db import DB

collection = DB["ParentID"]

def search_parent(chat_id):
    try:
        result = collection.find_one({"chat_id": chat_id})
        if result:
            return result["parent_id"]
        return "root"
    except Exception as e:
        print(f"MongoDB idsDB search error: {e}")
        return "root"

def _set(chat_id, parent_id):
    try:
        collection.update_one(
            {"chat_id": chat_id},
            {"$set": {"parent_id": parent_id}},
            upsert=True
        )
    except Exception as e:
        print(f"MongoDB idsDB set error: {e}")

def _clear(chat_id):
    try:
        collection.delete_one({"chat_id": chat_id})
    except Exception as e:
        print(f"MongoDB idsDB clear error: {e}")
