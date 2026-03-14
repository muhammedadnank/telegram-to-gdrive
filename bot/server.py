import os
import logging
import urllib.request
from flask import Flask, request, render_template_string
from threading import Thread

LOGGER = logging.getLogger(__name__)

app = Flask(__name__)

# Shared dict to pass auth code from web callback to bot
oauth_callbacks = {}


@app.route('/')
def home():
    return "Bot is running! 🎵"


@app.route('/health')
def health():
    return {"status": "ok"}, 200


@app.route('/oauth2callback')
def oauth2callback():
    code = request.args.get('code')
    error = request.args.get('error')

    if error:
        return render_template_string("""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>❌ Authorization Failed</h2>
        <p>Error: {{ error }}</p>
        <p>Please try again using /auth in the bot.</p>
        </body></html>
        """, error=error), 400

    if code:
        # Store code temporarily — bot will pick it up by state/user_id
        # We display the code for the user to send to the bot
        return render_template_string("""
        <html><body style="font-family:sans-serif;text-align:center;padding:50px">
        <h2>✅ Authorization Successful!</h2>
        <p>Copy the code below and send it to the bot:</p>
        <div style="background:#f0f0f0;padding:15px;border-radius:8px;font-size:1.2em;
                    font-family:monospace;word-break:break-all;margin:20px auto;max-width:600px">
            {{ code }}
        </div>
        <p style="color:gray">Go back to Telegram and paste this code in the chat.</p>
        </body></html>
        """, code=code)

    return "No code received.", 400


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
    port = int(os.environ.get("PORT", 10000))
    LOGGER.info(f"Starting Flask server on port {port}")
    app.run(host='0.0.0.0', port=port)


def start_server():
    # Start Flask server
    flask_thread = Thread(target=run, daemon=True)
    flask_thread.start()

    # Start keep-alive pinger
    ping_thread = Thread(target=keep_alive_ping, daemon=True)
    ping_thread.start()
