"""
gDriveDB — multi-account OAuth credential store.

Schema per document:
{
    "chat_id": <int>,
    "accounts": [
        {"label": "user@gmail.com", "creds": "<json string>"},
        ...
    ],
    "active": 0   # index into accounts list
}
"""
import json
from oauth2client.client import OAuth2Credentials
from bot.helpers.db import DB

collection = DB["gDrive"]


# ── internal helpers ──────────────────────────────────────────────────────────

def _get_doc(chat_id):
    return collection.find_one({"chat_id": chat_id})


def _save_doc(chat_id, accounts, active=0):
    collection.update_one(
        {"chat_id": chat_id},
        {"$set": {"accounts": accounts, "active": active}},
        upsert=True,
    )


# ── public API ────────────────────────────────────────────────────────────────

def search(chat_id) -> OAuth2Credentials | None:
    """Return the *active* OAuth2Credentials for this user, or None."""
    try:
        doc = _get_doc(chat_id)
        if not doc or not doc.get("accounts"):
            return None
        idx = doc.get("active", 0)
        accounts = doc["accounts"]
        if idx >= len(accounts):
            idx = 0
        return OAuth2Credentials.from_json(accounts[idx]["creds"])
    except Exception as e:
        print(f"MongoDB gDriveDB search error: {e}")
        return None


def _set(chat_id, credential, label: str | None = None):
    """
    Update (or create) an account entry for chat_id.
    • If an existing account has the same email/label it is updated in-place.
    • Otherwise a new account is appended and made active.
    Returns the 0-based index of the account that was set.
    """
    try:
        creds_json = credential.to_json()
        # Try to derive label from token info
        if label is None:
            try:
                info = json.loads(creds_json)
                label = info.get("id_token", {}).get("email") or f"Account"
            except Exception:
                label = "Account"

        doc = _get_doc(chat_id)
        if doc and doc.get("accounts"):
            accounts = doc["accounts"]
            active = doc.get("active", 0)
            # Check for duplicate label
            for i, acc in enumerate(accounts):
                if acc.get("label") == label:
                    accounts[i]["creds"] = creds_json
                    _save_doc(chat_id, accounts, active=i)
                    return i
            # New account
            accounts.append({"label": label, "creds": creds_json})
            new_idx = len(accounts) - 1
            _save_doc(chat_id, accounts, active=new_idx)
            return new_idx
        else:
            _save_doc(chat_id, [{"label": label, "creds": creds_json}], active=0)
            return 0
    except Exception as e:
        print(f"MongoDB gDriveDB set error: {e}")
        return -1


def _clear(chat_id, index: int | None = None):
    """
    Remove one account (by index) or ALL accounts.
    • index=None  → delete the entire document
    • index=int   → remove that account; shift active if needed
    """
    try:
        doc = _get_doc(chat_id)
        if not doc:
            return

        if index is None:
            collection.delete_one({"chat_id": chat_id})
            return

        accounts = doc.get("accounts", [])
        if index < 0 or index >= len(accounts):
            return  # out of range, nothing to do

        accounts.pop(index)
        if not accounts:
            collection.delete_one({"chat_id": chat_id})
            return

        active = doc.get("active", 0)
        if active >= len(accounts):
            active = len(accounts) - 1
        elif active > index:
            active -= 1

        _save_doc(chat_id, accounts, active=active)
    except Exception as e:
        print(f"MongoDB gDriveDB clear error: {e}")


def list_accounts(chat_id) -> list[dict]:
    """
    Return list of {"index": int, "label": str, "active": bool}.
    """
    try:
        doc = _get_doc(chat_id)
        if not doc or not doc.get("accounts"):
            return []
        active = doc.get("active", 0)
        return [
            {"index": i, "label": acc["label"], "active": i == active}
            for i, acc in enumerate(doc["accounts"])
        ]
    except Exception as e:
        print(f"MongoDB gDriveDB list_accounts error: {e}")
        return []


def switch_account(chat_id, index: int) -> bool:
    """Switch active account. Returns True on success."""
    try:
        doc = _get_doc(chat_id)
        if not doc or not doc.get("accounts"):
            return False
        if index < 0 or index >= len(doc["accounts"]):
            return False
        _save_doc(chat_id, doc["accounts"], active=index)
        return True
    except Exception as e:
        print(f"MongoDB gDriveDB switch_account error: {e}")
        return False


def count(chat_id) -> int:
    """Return number of linked accounts for user."""
    try:
        doc = _get_doc(chat_id)
        if not doc:
            return 0
        return len(doc.get("accounts", []))
    except Exception:
        return 0
