import os
from httplib2 import Http
from bot import LOGGER, G_DRIVE_CLIENT_ID, G_DRIVE_CLIENT_SECRET
from bot.config import Messages
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from oauth2client.client import OAuth2WebServerFlow, FlowExchangeError, HttpAccessTokenRefreshError
from bot.helpers.db import gDriveDB
from bot.config import BotCommands
from bot.helpers.utils import CustomFilters


OAUTH_SCOPE = "https://www.googleapis.com/auth/drive"
REDIRECT_URI = os.environ.get("REDIRECT_URI", "")

flows = {}


@Client.on_message(
    filters.private & filters.incoming & filters.command(BotCommands.Authorize)
)
async def _auth(client, message):
    user_id = message.from_user.id
    if not G_DRIVE_CLIENT_ID or not G_DRIVE_CLIENT_SECRET:
        await message.reply_text(
            "❗ **Google Drive OAuth credentials are not configured.**\n"
            "__The administrator has not set `G_DRIVE_CLIENT_ID` and `G_DRIVE_CLIENT_SECRET` in the environment variables.__\n"
            "__This is required for personal Google Drive authorization/upload. Please contact the administrator.__",
            quote=True
        )
        return

    creds = gDriveDB.search(user_id)
    if creds is not None:
        try:
            creds.refresh(Http())
            gDriveDB._set(user_id, creds)
            await message.reply_text(Messages.ALREADY_AUTH, quote=True)
        except HttpAccessTokenRefreshError:
            LOGGER.warning(f"Token refresh failed for {user_id} — clearing creds")
            gDriveDB._clear(user_id)
            await message.reply_text(
                "⚠️ **Your Google authorization has expired or been revoked.**\n"
                "__Your old session has been cleared. Please re-authorize below.__",
                quote=True,
            )
            await _send_auth_url(message, user_id)
    else:
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


@Client.on_message(
    filters.private
    & filters.incoming
    & filters.command(BotCommands.Revoke)
    & CustomFilters.auth_users
)
async def _revoke(client, message):
    user_id = message.from_user.id
    try:
        gDriveDB._clear(user_id)
        LOGGER.info(f"Revoked:{user_id}")
        await message.reply_text(Messages.REVOKED, quote=True)
    except Exception as e:
        await message.reply_text(f"**ERROR:** `{e}`", quote=True)


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
                gDriveDB._set(user_id, creds)
                LOGGER.info(f"AuthSuccess: {user_id}")
                await sent_message.edit(Messages.AUTH_SUCCESSFULLY)
                del flows[user_id]
            except FlowExchangeError:
                await sent_message.edit(Messages.INVALID_AUTH_CODE)
            except Exception as e:
                await sent_message.edit(f"**ERROR:** `{e}`")
        else:
            await message.reply_text(Messages.FLOW_IS_NONE, quote=True)
    else:
        # Not an auth code — guide unauthorized users to /start
        await message.reply_text(
            f"👋 **Please authenticate first.**\n__Use /auth to connect your Google Drive.__",
            quote=True,
        )
