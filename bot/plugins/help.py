from pyrogram import Client, filters
from bot.config import Messages as tr


@Client.on_message(
    filters.private & filters.incoming & filters.command(["start"]), group=2
)
async def _start(client, message):
    await client.send_message(
        chat_id=message.chat.id,
        text=tr.START_MSG.format(message.from_user.mention),
        reply_to_message_id=message.id,
    )


@Client.on_message(
    filters.private & filters.incoming & filters.command(["help"]), group=2
)
async def _help(client, message):
    for msg in tr.HELP_MSG[1:]:
        await message.reply_text(msg, quote=True)
