import os
import asyncio
from pyrogram import Client, filters
from pyrogram.errors import RPCError, FloodWait
from bot.helpers.utils import CustomFilters, humanbytes
from bot.helpers.gdrive_utils import GoogleDrive
from bot import DOWNLOAD_DIRECTORY, LOGGER
from bot.config import Messages


@Client.on_message(
    filters.private
    & filters.incoming
    & (filters.document | filters.audio)
    & CustomFilters.auth_users
)
async def _telegram_file(client, message):
    user_id = message.from_user.id
    file_path = None  # Initialize to avoid UnboundLocalError

    sent_message = await message.reply_text("🕵️**Checking File...**", quote=True)

    if message.document:
        file = message.document
    elif message.audio:
        file = message.audio

    # Only allow audio/music mime types
    if not file.mime_type.startswith("audio/"):
        await sent_message.edit(
            "❗ **Only music/audio files are supported.**\n__Send an audio file (mp3, flac, wav, etc.)__"
        )
        return

    await sent_message.edit(
        Messages.DOWNLOAD_TG_FILE.format(
            file.file_name, humanbytes(file.file_size), file.mime_type
        )
    )
    LOGGER.info(f"Download:{user_id}: {file.file_name}")

    try:
        file_path = await message.download(file_name=DOWNLOAD_DIRECTORY)
        await sent_message.edit(
            Messages.DOWNLOADED_SUCCESSFULLY.format(
                os.path.basename(file_path), humanbytes(os.path.getsize(file_path))
            )
        )
        msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type)
        await sent_message.edit(msg)

    except FloodWait as e:
        wait_seconds = e.value
        LOGGER.warning(f"FloodWait for {user_id}: waiting {wait_seconds} seconds")
        await sent_message.edit(
            f"⏳ **Telegram Rate Limit.**\n__Too many requests. Waiting {wait_seconds} seconds before retrying...__"
        )
        await asyncio.sleep(wait_seconds)
        # Retry after wait
        try:
            file_path = await message.download(file_name=DOWNLOAD_DIRECTORY)
            await sent_message.edit(
                Messages.DOWNLOADED_SUCCESSFULLY.format(
                    os.path.basename(file_path), humanbytes(os.path.getsize(file_path))
                )
            )
            msg = GoogleDrive(user_id).upload_file(file_path, file.mime_type)
            await sent_message.edit(msg)
        except Exception as retry_e:
            LOGGER.error(f"Retry failed for {user_id}: {retry_e}")
            await sent_message.edit(Messages.WENT_WRONG)

    except RPCError as e:
        LOGGER.error(f"RPCError for {user_id}: {e}")
        await sent_message.edit(Messages.WENT_WRONG)

    except Exception as e:
        LOGGER.error(f"Unexpected error for {user_id}: {e}")
        await sent_message.edit(Messages.WENT_WRONG)

    finally:
        # Always cleanup — only if file was actually downloaded
        if file_path and os.path.exists(file_path):
            LOGGER.info(f"Deleting: {file_path}")
            os.remove(file_path)
