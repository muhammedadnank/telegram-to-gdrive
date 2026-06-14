from pyrogram import Client, filters
from pyrogram.types import Message


HELP_TEXT = """**🎵 Google Drive & Telegram Music Bot**

This bot supports dual-sync operations simultaneously:

**1️⃣ Google Drive ➔ Telegram Sync (Automatic)**
Syncs audio files from mapped Google Drive folders to Telegram channels.
*Admin Commands:*
• `/addfolder <folder_url> <channel_id>` — Map a Drive folder to a channel
• `/removefolder <folder_id>` — Remove a folder mapping
• `/status` — Bot status and active mappings
• `/stats` — Upload statistics
• `/last` — Last uploaded file details
• `/sync` — Trigger immediate Drive check
• `/retry` — Retry failed uploads
• `/logs` — Get bot logs

**2️⃣ Telegram ➔ Google Drive Upload**
Send any audio/music file directly to this bot, and it will upload it to your Google Drive.
*User Commands:*
• `/auth` — Authenticate your Google Drive account
• `/revoke` — Revoke your authenticated Google Drive account
• `/setfolder <folder_url>` — Set custom upload folder (or `/setfolder clear`)

**Supported audio formats:** MP3, M4A, FLAC, WAV, AAC, OGG, OPUS"""


@Client.on_message(filters.private & filters.command("start"))
async def cmd_start(client: Client, message: Message):
    await message.reply_text(
        f"👋 **Hi {message.from_user.mention}!**\n\n"
        "I sync audio files from Google Drive folders to Telegram channels automatically.\n\n"
        "Use /help to see available commands.",
        quote=True,
    )


@Client.on_message(filters.private & filters.command("help"))
async def cmd_help(client: Client, message: Message):
    await message.reply_text(HELP_TEXT, quote=True)
