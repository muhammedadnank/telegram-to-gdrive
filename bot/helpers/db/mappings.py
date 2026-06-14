from bot.helpers.db import DB

_col = DB["folder_mappings"]


def add(folder_id: str, channel_id: str, added_by: int = None) -> bool:
    """Add or re-enable a folder➔channel mapping."""
    try:
        update_data = {
            "folder_id": folder_id,
            "channel_id": channel_id,
            "enabled": True,
        }
        if added_by is not None:
            update_data["added_by"] = added_by
        _col.update_one(
            {"folder_id": folder_id},
            {"$set": update_data},
            upsert=True,
        )
        return True
    except Exception as e:
        print(f"mappings.add error: {e}")
        return False


def remove(folder_id: str) -> bool:
    """Disable a mapping (soft delete)."""
    try:
        result = _col.update_one({"folder_id": folder_id}, {"$set": {"enabled": False}})
        return result.modified_count > 0
    except Exception as e:
        print(f"mappings.remove error: {e}")
        return False


def get(folder_id: str) -> dict:
    """Return the folder mapping document."""
    try:
        return _col.find_one({"folder_id": folder_id}, {"_id": 0})
    except Exception as e:
        print(f"mappings.get error: {e}")
        return None


def get_all_enabled() -> list:
    """Return all enabled folder→channel mappings."""
    try:
        return list(_col.find({"enabled": True}, {"_id": 0}))
    except Exception as e:
        print(f"mappings.get_all_enabled error: {e}")
        return []


def get_all() -> list:
    try:
        return list(_col.find({}, {"_id": 0}))
    except Exception as e:
        print(f"mappings.get_all error: {e}")
        return []

