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
logging.getLogger("googleapiclient.discovery").setLevel(logging.ERROR)

try:
    BOT_TOKEN = os.environ["BOT_TOKEN"]
    APP_ID = int(os.environ["APP_ID"])
    API_HASH = os.environ["API_HASH"]
    MONGO_URI = os.environ["MONGO_URI"]

    _sudo_raw = os.environ.get("SUDO_USERS", "")
    SUDO_USERS = list(set(int(x) for x in _sudo_raw.split() if x))

    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "3"))
    POLL_INTERVAL = int(os.environ.get("POLL_INTERVAL", "45"))
    DOWNLOAD_DIRECTORY = os.environ.get("DOWNLOAD_DIRECTORY", "./downloads/")
    FAILED_DIRECTORY = os.environ.get("FAILED_DIRECTORY", "./failed/")

    G_DRIVE_CLIENT_ID = os.environ["G_DRIVE_CLIENT_ID"]
    G_DRIVE_CLIENT_SECRET = os.environ["G_DRIVE_CLIENT_SECRET"]
    REDIRECT_URI = os.environ.get("REDIRECT_URI", "")
    if REDIRECT_URI and not REDIRECT_URI.endswith("/oauth2callback"):
        if REDIRECT_URI.endswith("/"):
            REDIRECT_URI += "oauth2callback"
        else:
            REDIRECT_URI += "/oauth2callback"
    WEB_PASSWORD = os.environ.get("WEB_PASSWORD", "")

except KeyError as e:
    LOGGER.error(f"Missing required environment variable: {e}")
    exit(1)
except ValueError as e:
    LOGGER.error(f"Invalid environment variable value: {e}")
    exit(1)
