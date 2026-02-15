import os
import logging
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    handlers=[logging.FileHandler("log.txt"), logging.StreamHandler()],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
LOGGER = logging.getLogger(__name__)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

try:
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    APP_ID = int(os.environ["APP_ID"])
    API_HASH = os.environ["API_HASH"]
    MONGO_URI = os.environ["MONGO_URI"]
    SUDO_USERS = os.environ.get("SUDO_USERS", "")
    SUPPORT_CHAT_LINK = os.environ.get("SUPPORT_CHAT_LINK", "")
    DOWNLOAD_DIRECTORY = os.environ.get("DOWNLOAD_DIRECTORY", "./downloads/")
    G_DRIVE_CLIENT_ID = os.environ.get("G_DRIVE_CLIENT_ID")
    G_DRIVE_CLIENT_SECRET = os.environ.get("G_DRIVE_CLIENT_SECRET")

    sudo_users_list = [int(x) for x in SUDO_USERS.split()] if SUDO_USERS else []
    SUDO_USERS = list(set(sudo_users_list))
except KeyError as e:
    LOGGER.error(f"Mandatory environment variable {e} is missing. Exiting now.")
    exit(1)
except ValueError as e:
    LOGGER.error(f"Invalid value for environment variable: {e}. Exiting now.")
    exit(1)
