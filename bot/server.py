import os
import logging
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


def run():
    port = int(os.environ.get("PORT", 8080))
    LOGGER.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)


def start_server():
    t = Thread(target=run, daemon=True)
    t.daemon = True
    t.start()
