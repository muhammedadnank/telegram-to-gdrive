import os
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


if __name__ == "__main__":
    # Create downloads directory if not exists
    if not os.path.isdir(DOWNLOAD_DIRECTORY):
        os.makedirs(DOWNLOAD_DIRECTORY)

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
        workdir=".",  # Save session file in root, not downloads folder
    )

    LOGGER.info("Starting Bot!")
    app.run()
    LOGGER.info("Bot Stopped!")
