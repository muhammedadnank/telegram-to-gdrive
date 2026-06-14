import os
import json
import signal
import asyncio
import logging

from pyrogram import Client
from pyrogram import enums

from bot import (
    BOT_TOKEN, APP_ID, API_HASH,
    DOWNLOAD_DIRECTORY, FAILED_DIRECTORY,
    LOGGER,
)
from bot.server import start_server
from bot.helpers.gdrive import DriveMonitor
from bot.helpers.db import uploads as uploads_db

logging.getLogger("pyrogram").setLevel(logging.WARNING)





def _ensure_dirs():
    import shutil
    project_root = os.path.abspath(".")
    download_abs = os.path.abspath(DOWNLOAD_DIRECTORY)
    failed_abs = os.path.abspath(FAILED_DIRECTORY)

    # Safety: never wipe root, project dir, or the failed/ dir itself
    safe_to_wipe = (
        os.path.isdir(download_abs)
        and download_abs != project_root
        and download_abs != failed_abs
        and not failed_abs.startswith(download_abs + os.sep)
    )
    if safe_to_wipe:
        try:
            shutil.rmtree(download_abs)
            LOGGER.info(f"Cleared download directory: {download_abs}")
        except Exception as e:
            LOGGER.warning(f"Failed to clear download directory: {e}")

    for d in [DOWNLOAD_DIRECTORY, FAILED_DIRECTORY,
              os.path.join(DOWNLOAD_DIRECTORY, "drive"),
              os.path.join(DOWNLOAD_DIRECTORY, "tg")]:
        os.makedirs(d, exist_ok=True)


async def _run():
    _ensure_dirs()
    start_server()

    plugins = dict(root="bot/plugins")
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Client(
        "GDriveSyncBot",
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        plugins=plugins,
        parse_mode=enums.ParseMode.MARKDOWN,
        workdir=base_dir,
    )

    monitor = DriveMonitor(pyrogram_client=app)
    app._drive_monitor = monitor  # expose to plugins via client ref

    import bot.server
    bot.server.monitor = monitor
    bot.server.loop = asyncio.get_running_loop()

    async with app:
        LOGGER.info("Bot started.")

        # Reset any stale/stuck uploads from previous sessions
        uploads_db.reset_stale_uploads()

        # Startup: auto-retry any previously failed uploads
        retry_count = await monitor.enqueue_retryable()
        if retry_count:
            LOGGER.info(f"Startup auto-retry: {retry_count} item(s) re-queued.")

        await monitor.start()

        stop_event = asyncio.Event()

        def _handle_sigterm(*_):
            LOGGER.info("SIGTERM received — shutting down gracefully.")
            stop_event.set()

        signal.signal(signal.SIGTERM, _handle_sigterm)
        signal.signal(signal.SIGINT, _handle_sigterm)

        await stop_event.wait()
        await monitor.stop()
        LOGGER.info("Bot stopped.")


if __name__ == "__main__":
    asyncio.run(_run())
