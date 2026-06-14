import os
from httplib2 import Http
from bot import LOGGER, G_DRIVE_CLIENT_ID, G_DRIVE_CLIENT_SECRET
from bot.config import Messages, BotCommands
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError, HttpAccessTokenRefreshError
from bot.helpers.db import gDriveDB
from bot.helpers.utils import CustomFilters


OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
REDIRECT_URI = os.environ.get("REDIRECT_URI", "")

# Pending auth flows keyed by user_id
flows = {}


def _no_oauth_configured(message):
    return not G_DRIVE_CLIENT_ID or not G_DRIVE_CLIENT_SECRET


# ── /auth — start OAuth flow (always adds a new account) ─────────────────────

@Client.on_message(
    filters.private & filters.incoming & filters.command(BotCommands.Authorize)
)
async def _auth(client, message):
    if _no_oauth_configured(message):
        await message.reply_text(
            "❗ **Google Drive OAuth credentials are not configured.**\n"
            "__The administrator has not set `G_DRIVE_CLIENT_ID` and `G_DRIVE_CLIENT_SECRET`.__",
            quote=True,
        )
        return

    user_id = message.from_user.id
    existing = gDriveDB.list_accounts(user_id)
    if existing:
        await message.reply_text(
            Messages.ALREADY_AUTH.format(count=len(existing)),
            quote=True,
        )
        # Still fall through so the user can add another account
    await _send_auth_url(message, user_id)


async def _send_auth_url(message, user_id):
    try:
        flow_kwargs = dict(
            client_id=G_DRIVE_CLIENT_ID,
            client_secret=G_DRIVE_CLIENT_SECRET,
            scope=OAUTH_SCOPE,
            response_type="code",
            access_type="offline",
            prompt="consent",
        )
        if REDIRECT_URI:
            flow_kwargs["redirect_uri"] = REDIRECT_URI

        flow = OAuth2WebServerFlow(**flow_kwargs)
        auth_url = flow.step1_get_authorize_url()
        flows[user_id] = flow
        LOGGER.info(f"AuthURL:{user_id}")
        await message.reply_text(
            text=Messages.AUTH_TEXT.format(auth_url),
            quote=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Authorization URL", url=auth_url)]]
            ),
        )
    except Exception as e:
        await message.reply_text(f"**ERROR:** `{e}`", quote=True)


# ── /accounts — list all linked Drive accounts ────────────────────────────────

@Client.on_message(
    filters.private & filters.incoming & filters.command(BotCommands.Accounts)
)
async def _accounts(client, message):
    user_id = message.from_user.id
    accounts = gDriveDB.list_accounts(user_id)
    if not accounts:
        await message.reply_text(Messages.NO_ACCOUNTS, quote=True)
        return

    lines = []
    for acc in accounts:
        star = "⭐" if acc["active"] else "  "
        lines.append(f"{star} **#{acc['index'] + 1}** — `{acc['label']}`")

    await message.reply_text(
        Messages.ACCOUNTS_LIST_HEADER.format(entries="\n".join(lines)),
        quote=True,
    )


# ── /switch <number> — change active account ──────────────────────────────────

@Client.on_message(
    filters.private & filters.incoming & filters.command(BotCommands.SwitchAccount)
)
async def _switch(client, message):
    user_id = message.from_user.id
    accounts = gDriveDB.list_accounts(user_id)
    if not accounts:
        await message.reply_text(Messages.NO_ACCOUNTS, quote=True)
        return

    parts = message.command
    if len(parts) < 2 or not parts[1].isdigit():
        # Show current list with usage hint
        lines = [
            f"{'⭐' if a['active'] else '  '} **#{a['index'] + 1}** — `{a['label']}`"
            for a in accounts
        ]
        await message.reply_text(
            "**Usage:** `/switch <number>`\n\n" + "\n".join(lines),
            quote=True,
        )
        return

    idx = int(parts[1]) - 1  # user-facing is 1-based
    ok = gDriveDB.switch_account(user_id, idx)
    if ok:
        label = accounts[idx]["label"] if idx < len(accounts) else "?"
        await message.reply_text(
            Messages.SWITCHED.format(index=idx + 1, label=label),
            quote=True,
        )
    else:
        await message.reply_text(
            f"❗ **Invalid account number.** You have {len(accounts)} account(s).",
            quote=True,
        )


# ── /revoke [number] — remove one account or active account ──────────────────

@Client.on_message(
    filters.private & filters.incoming & filters.command(BotCommands.Revoke)
)
async def _revoke(client, message):
    user_id = message.from_user.id
    accounts = gDriveDB.list_accounts(user_id)
    if not accounts:
        await message.reply_text(Messages.NO_ACCOUNTS, quote=True)
        return

    parts = message.command
    if len(parts) >= 2 and parts[1].isdigit():
        idx = int(parts[1]) - 1
    else:
        # Default: remove the active account
        idx = next((a["index"] for a in accounts if a["active"]), 0)

    if idx < 0 or idx >= len(accounts):
        await message.reply_text(
            f"❗ **Invalid account number.** You have {len(accounts)} account(s).",
            quote=True,
        )
        return

    label = accounts[idx]["label"]
    try:
        gDriveDB._clear(user_id, index=idx)
        LOGGER.info(f"Revoked account #{idx + 1} ({label}) for {user_id}")
        await message.reply_text(
            f"🔓 **Account #{idx + 1} (`{label}`) removed.**\n" + Messages.REVOKED,
            quote=True,
        )
    except Exception as e:
        await message.reply_text(f"**ERROR:** `{e}`", quote=True)


# ── Incoming text — exchange OAuth code ───────────────────────────────────────

@Client.on_message(
    filters.private
    & filters.incoming
    & filters.text
    & ~filters.regex(r"^/")
    & ~CustomFilters.auth_users
)
async def _token(client, message):
    code = message.text
    token = code.split()[-1]
    if token.startswith("4/"):
        user_id = message.from_user.id
        if user_id in flows:
            try:
                sent_message = await message.reply_text(
                    "🕵️**Checking received code...**", quote=True
                )
                creds = flows[user_id].step2_exchange(token)
                idx = gDriveDB._set(user_id, creds)
                LOGGER.info(f"AuthSuccess: {user_id} → account #{idx + 1}")
                accounts = gDriveDB.list_accounts(user_id)
                label = accounts[idx]["label"] if idx < len(accounts) else "?"
                await sent_message.edit(
                    Messages.AUTH_SUCCESSFULLY.format(index=idx + 1, label=label)
                )
                del flows[user_id]
            except FlowExchangeError:
                await sent_message.edit(Messages.INVALID_AUTH_CODE)
            except Exception as e:
                await sent_message.edit(f"**ERROR:** `{e}`")
        else:
            await message.reply_text(Messages.FLOW_IS_NONE, quote=True)
    else:
        await message.reply_text(
            f"👋 **Please authenticate first.**\n__Use /auth to connect your Google Drive.__",
            quote=True,
        )
