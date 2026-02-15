import os
import logging
import threading
import urllib.request
from flask import Flask
from threading import Thread

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)


@app.route('/')
def home():
    return "Bot is running! 🎵"


@app.route('/health')
def health():
    return {"status": "ok"}, 200


def keep_alive_ping():
    """Ping own server every 10 minutes to prevent Render free tier sleep."""
    import time
    render_url = os.environ.get("RENDER_EXTERNAL_URL")
    if not render_url:
        LOGGER.info("RENDER_EXTERNAL_URL not set, keep-alive ping disabled.")
        return
    while True:
        time.sleep(600)  # 10 minutes
        try:
            urllib.request.urlopen(f"{render_url}/health", timeout=10)
            LOGGER.info("Keep-alive ping sent.")
        except Exception as e:
            LOGGER.warning(f"Keep-alive ping failed: {e}")


def run():
    port = int(os.environ.get("PORT", 8080))
    LOGGER.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)


def start_server():
    # Start Flask server
    flask_thread = Thread(target=run, daemon=True)
    flask_thread.start()

    # Start keep-alive pinger
    ping_thread = Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()
