from os import execl
from sys import executable
from pyrogram import Client, filters
from bot import SUDO_USERS, LOGGER


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

