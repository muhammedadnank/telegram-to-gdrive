from datetime import datetime, timezone
from bot.helpers.db import DB

_col = DB["uploads"]

AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".opus"}


def is_uploaded(file_id: str) -> bool:
    """Return True if file was already successfully uploaded."""
    try:
        doc = _col.find_one({"file_id": file_id, "status": "completed"})
        return doc is not None
    except Exception as e:
        print(f"uploads.is_uploaded error: {e}")
        return False


def create_pending(file_id: str, file_name: str, folder_id: str, channel_id: str):
    """Insert a new pending record."""
    try:
        _col.update_one(
            {"file_id": file_id},
            {
                "$setOnInsert": {
                    "file_id": file_id,
                    "file_name": file_name,
                    "folder_id": folder_id,
                    "channel_id": channel_id,
                    "status": "pending",
                    "retry_count": 0,
                    "uploaded_at": None,
                }
            },
            upsert=True,
        )
    except Exception as e:
        print(f"uploads.create_pending error: {e}")


def set_status(file_id: str, status: str):
    try:
        update = {"$set": {"status": status}}
        if status == "completed":
            update["$set"]["uploaded_at"] = datetime.now(timezone.utc)
        _col.update_one({"file_id": file_id}, update)
    except Exception as e:
        print(f"uploads.set_status error: {e}")


def increment_retry(file_id: str) -> int:
    """Increment retry_count, set status=failed, return new count."""
    try:
        result = _col.find_one_and_update(
            {"file_id": file_id},
            {"$inc": {"retry_count": 1}, "$set": {"status": "failed"}},
            return_document=True,
        )
        return result["retry_count"] if result else 0
    except Exception as e:
        print(f"uploads.increment_retry error: {e}")
        return 0


def get_retryable() -> list:
    """Return failed records with retry_count < 3."""
    try:
        return list(_col.find({"status": "failed", "retry_count": {"$lt": 3}}))
    except Exception as e:
        print(f"uploads.get_retryable error: {e}")
        return []


def reset_for_retry(file_id: str):
    try:
        _col.update_one({"file_id": file_id}, {"$set": {"status": "pending"}})
    except Exception as e:
        print(f"uploads.reset_for_retry error: {e}")


def reset_stale_uploads():
    """Reset any stuck uploads (pending, downloading, uploading) to failed on startup."""
    try:
        _col.update_many(
            {"status": {"$in": ["pending", "downloading", "uploading"]}},
            {"$set": {"status": "failed"}}
        )
    except Exception as e:
        print(f"uploads.reset_stale_uploads error: {e}")


def get_stats() -> dict:
    try:
        total = _col.count_documents({})
        completed = _col.count_documents({"status": "completed"})
        failed = _col.count_documents({"status": "failed"})
        pending = _col.count_documents({"status": {"$in": ["pending", "downloading", "uploading"]}})
        return {"total": total, "completed": completed, "failed": failed, "pending": pending}
    except Exception as e:
        print(f"uploads.get_stats error: {e}")
        return {}


def get_last_completed():
    try:
        return _col.find_one({"status": "completed"}, sort=[("uploaded_at", -1)])
    except Exception as e:
        print(f"uploads.get_last error: {e}")
        return None
