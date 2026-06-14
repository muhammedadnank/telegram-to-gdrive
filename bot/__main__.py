import os
import signal
import logging
from pyrogram import Client
from pyrogram import enums
from bot import APP_ID, API_HASH, BOT_TOKEN, DOWNLOAD_DIRECTORY
from bot.server import start_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)


def handle_sigterm(signum, frame):
    LOGGER.info("SIGTERM received — bot will stop gracefully after current upload completes.")


if __name__ == "__main__":
    # Handle Render's SIGTERM gracefully
    signal.signal(signal.SIGTERM, handle_sigterm)

    # Use absolute path for downloads to avoid path confusion
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    download_dir = os.path.join(base_dir, "downloads")

    import shutil
    if os.path.isdir(download_dir):
        try:
            shutil.rmtree(download_dir)
        except Exception as e:
            LOGGER.warning(f"Failed to clear download directory: {e}")
    os.makedirs(download_dir)

    LOGGER.info(f"Download directory: {download_dir}")

    # Start Flask keep-alive server
    start_server()

    plugins = dict(root="bot/plugins")

    app = Client(
        "G-DriveBot",
        bot_token=BOT_TOKEN,
        api_id=APP_ID,
        api_hash=API_HASH,
        plugins=plugins,
        parse_mode=enums.ParseMode.MARKDOWN,
        workdir=base_dir,
    )

    LOGGER.info("Starting Bot!")
    app.run()
    LOGGER.info("Bot Stopped!")
