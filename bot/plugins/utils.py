import os
import shutil
from os import execl
from time import sleep
from sys import executable
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError
from bot import SUDO_USERS, DOWNLOAD_DIRECTORY, LOGGER


@Client.on_message(
    filters.private
    & filters.incoming
    & filters.command(["logs"])
    & filters.user(SUDO_USERS),
    group=2,
)
async def _send_log(client, message):
    with open("log.txt", "rb") as f:
        try:
            await client.send_document(
                message.chat.id,
                document=f,
                file_name=f.name,
                reply_to_message_id=message.id,
            )
            LOGGER.info(f"Log file sent to {message.from_user.id}")
        except FloodWait as e:
            sleep(e.value)  # Fixed: e.x → e.value (Pyrofork)
        except RPCError as e:
            await message.reply_text(e, quote=True)


@Client.on_message(
    filters.private
    & filters.incoming
    & filters.command(["restart"])
    & filters.user(SUDO_USERS),
    group=2,
)
async def _restart(client, message):
    await message.reply_text("**♻️ Restarting...**", quote=True)
    LOGGER.info(f"{message.from_user.id}: Restarting...")
    # Recreate download dir cleanly after restart instead of deleting before
    execl(executable, executable, "-m", "bot")
