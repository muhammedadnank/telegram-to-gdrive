import os
import logging
import asyncio
from flask import Flask, request, render_template_string
from threading import Thread

from bot import WEB_PASSWORD
from bot.helpers.db import uploads as uploads_db
from bot.helpers.db import mappings as mappings_db

LOGGER = logging.getLogger(__name__)
app = Flask(__name__)

# Global references to DriveMonitor and asyncio event loop
monitor = None
loop = None

DASHBOARD_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Google Drive ➔ Telegram Sync Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;800&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-color: #080710;
            --card-bg: rgba(255, 255, 255, 0.05);
            --border-color: rgba(255, 255, 255, 0.1);
            --text-primary: #ffffff;
            --text-secondary: #a0a5b5;
            --accent-green: #00ff87;
            --accent-blue: #60efff;
            --accent-red: #ff5e62;
            --glow-green: rgba(0, 255, 135, 0.15);
            --glow-blue: rgba(96, 239, 255, 0.15);
            --glow-red: rgba(255, 94, 98, 0.15);
        }
        
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(96, 239, 255, 0.05) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(0, 255, 135, 0.05) 0%, transparent 40%);
            color: var(--text-primary);
            font-family: 'Outfit', sans-serif;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 2rem;
            overflow-x: hidden;
        }

        .container {
            width: 100%;
            max-width: 800px;
            background: var(--card-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--border-color);
            border-radius: 24px;
            padding: 2.5rem;
            box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
            position: relative;
        }

        .header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 2.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 1.5rem;
        }

        .title-group h1 {
            font-size: 2rem;
            font-weight: 800;
            background: linear-gradient(45deg, #60efff, #00ff87);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            letter-spacing: -0.5px;
        }

        .title-group p {
            color: var(--text-secondary);
            font-size: 0.95rem;
            margin-top: 4px;
        }

        .status-badge {
            display: flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 255, 135, 0.1);
            border: 1px solid rgba(0, 255, 135, 0.2);
            padding: 8px 16px;
            border-radius: 99px;
            font-weight: 600;
            font-size: 0.85rem;
            color: var(--accent-green);
            box-shadow: 0 0 20px var(--glow-green);
        }

        .status-dot {
            width: 8px;
            height: 8px;
            background-color: var(--accent-green);
            border-radius: 50%;
            display: inline-block;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 255, 135, 0.7);
            }
            70% {
                transform: scale(1);
                box-shadow: 0 0 0 6px rgba(0, 255, 135, 0);
            }
            100% {
                transform: scale(0.95);
                box-shadow: 0 0 0 0 rgba(0, 255, 135, 0);
            }
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .stat-card {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            text-align: center;
            transition: all 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 255, 255, 0.2);
        }

        .stat-val {
            font-size: 2.25rem;
            font-weight: 800;
            margin-bottom: 4px;
        }

        .stat-val.completed {
            color: var(--accent-green);
            text-shadow: 0 0 15px var(--glow-green);
        }
        
        .stat-val.pending {
            color: var(--accent-blue);
            text-shadow: 0 0 15px var(--glow-blue);
        }

        .stat-val.failed {
            color: var(--accent-red);
            text-shadow: 0 0 15px var(--glow-red);
        }

        .stat-lbl {
            color: var(--text-secondary);
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Control Panel Styles */
        .control-panel {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 2.5rem;
        }

        .control-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 1.2rem;
        }

        .control-title {
            font-size: 1.1rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .password-container {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .password-input {
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 8px 12px;
            border-radius: 8px;
            font-family: inherit;
            font-size: 0.85rem;
            outline: none;
            transition: all 0.3s ease;
        }

        .password-input:focus {
            border-color: var(--accent-blue);
            box-shadow: 0 0 10px var(--glow-blue);
        }

        .btn-group {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1rem;
        }

        .btn {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
            background: linear-gradient(135deg, rgba(255,255,255,0.05) 0%, rgba(255,255,255,0.01) 100%);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 12px 20px;
            border-radius: 12px;
            font-family: inherit;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .btn::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transform: translateX(-100%);
        }

        .btn:hover:not(:disabled)::after {
            transform: translateX(100%);
            transition: transform 0.6s ease;
        }

        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
        }

        .btn:active:not(:disabled) {
            transform: translateY(1px);
        }

        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }

        .btn-sync:hover:not(:disabled) {
            border-color: var(--accent-blue);
            box-shadow: 0 0 15px var(--glow-blue);
            background: rgba(96, 239, 255, 0.05);
        }

        .btn-retry:hover:not(:disabled) {
            border-color: var(--accent-green);
            box-shadow: 0 0 15px var(--glow-green);
            background: rgba(0, 255, 135, 0.05);
        }

        .section-title {
            font-size: 1.2rem;
            font-weight: 600;
            margin-bottom: 1rem;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .mapping-list {
            display: flex;
            flex-direction: column;
            gap: 12px;
        }

        .mapping-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 1rem 1.5rem;
            border-radius: 12px;
            font-size: 0.95rem;
        }

        .folder-info {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .channel-info {
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--accent-blue);
            font-weight: 600;
        }

        .icon {
            width: 20px;
            height: 20px;
            fill: none;
            stroke: currentColor;
            stroke-width: 2;
            stroke-linecap: round;
            stroke-linejoin: round;
            opacity: 0.8;
        }

        .no-mappings {
            color: var(--text-secondary);
            font-style: italic;
            text-align: center;
            padding: 2rem;
            border: 1px dashed var(--border-color);
            border-radius: 12px;
        }

        /* Toast notifications */
        .toast-container {
            position: fixed;
            bottom: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 10px;
        }

        .toast {
            background: rgba(8, 7, 16, 0.95);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px 24px;
            color: var(--text-primary);
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            display: flex;
            align-items: center;
            gap: 12px;
            transform: translateY(100px);
            opacity: 0;
            transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
            backdrop-filter: blur(10px);
        }

        .toast.show {
            transform: translateY(0);
            opacity: 1;
        }

        .toast-success {
            border-left: 4px solid var(--accent-green);
        }

        .toast-error {
            border-left: 4px solid var(--accent-red);
        }

        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid rgba(255,255,255,0.3);
            border-radius: 50%;
            border-top-color: var(--text-primary);
            animation: spin 0.8s linear infinite;
            display: none;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        footer {
            margin-top: 2.5rem;
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        footer a {
            color: var(--accent-blue);
            text-decoration: none;
        }

        footer a:hover {
            text-decoration: underline;
        }

        @media (max-width: 600px) {
            .stats-grid {
                grid-template-columns: 1fr;
            }
            .btn-group {
                grid-template-columns: 1fr;
            }
            .header {
                flex-direction: column;
                align-items: flex-start;
                gap: 1rem;
            }
            .status-badge {
                align-self: flex-start;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="title-group">
                <h1>GDrive ➔ Telegram Hub</h1>
                <p>Real-time music synchronization service</p>
            </div>
            <div class="status-badge">
                <span class="status-dot"></span>
                ACTIVE
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-val completed">{{ stats.completed }}</div>
                <div class="stat-lbl">Completed</div>
            </div>
            <div class="stat-card">
                <div class="stat-val pending">{{ stats.pending }}</div>
                <div class="stat-lbl">Syncing</div>
            </div>
            <div class="stat-card">
                <div class="stat-val failed">{{ stats.failed }}</div>
                <div class="stat-lbl">Failed</div>
            </div>
        </div>

        <!-- Quick Actions Panel -->
        <div class="control-panel">
            <div class="control-header">
                <div class="control-title">
                    <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                        <line x1="6" y1="6" x2="6.01" y2="6"></line>
                        <line x1="6" y1="18" x2="6.01" y2="18"></line>
                    </svg>
                    Control Panel & Actions
                </div>
                {% if has_password %}
                <div class="password-container">
                    <input type="password" id="web-passcode" class="password-input" placeholder="Enter Web Password">
                </div>
                {% else %}
                <div style="font-size: 0.8rem; color: var(--text-secondary); opacity: 0.7;">
                    🔒 Unsecured Access (No password set)
                </div>
                {% endif %}
            </div>
            <div class="btn-group">
                <button id="btn-sync" class="btn btn-sync" onclick="triggerSync()">
                    <span class="spinner" id="spinner-sync"></span>
                    <svg class="icon" id="icon-sync" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21.5 2v6h-6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67"></path>
                    </svg>
                    Force Sync Drive
                </button>
                <button id="btn-retry" class="btn btn-retry" onclick="triggerRetry()">
                    <span class="spinner" id="spinner-retry"></span>
                    <svg class="icon" id="icon-retry" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M23 4v6h-6M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>
                    </svg>
                    Retry Failed Uploads
                </button>
            </div>
        </div>

        <div class="section-title">
            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
            </svg>
            Active Folders Mapped
        </div>

        <div class="mapping-list">
            {% if mappings %}
                {% for m in mappings %}
                    <div class="mapping-item">
                        <div class="folder-info">
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="#ffc107" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                                <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path>
                            </svg>
                            <code>{{ m.folder_id }}</code>
                        </div>
                        <div class="channel-info">
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-right: 4px;">
                                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
                            </svg>
                            <span>{{ m.channel_id }}</span>
                        </div>
                    </div>
                {% endfor %}
            {% else %}
                <div class="no-mappings">
                    No folders currently mapped. Use /addfolder in Telegram.
                </div>
            {% endif %}
        </div>
    </div>

    <div class="toast-container" id="toast-container"></div>

    <footer>
        Music Sync Bot v2.0 • Powered by Pyrogram & Flask
    </footer>

    <script>
        const passInput = document.getElementById('web-passcode');
        if (passInput) {
            passInput.value = localStorage.getItem('web_password') || '';
            passInput.addEventListener('input', (e) => {
                localStorage.setItem('web_password', e.target.value);
            });
        }

        function showToast(message, type = 'success') {
            const container = document.getElementById('toast-container');
            const toast = document.createElement('div');
            toast.className = `toast toast-${type}`;
            toast.innerHTML = `
                <span>${type === 'success' ? '✅' : '❌'}</span>
                <span>${message}</span>
            `;
            container.appendChild(toast);
            
            setTimeout(() => toast.classList.add('show'), 10);
            
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => toast.remove(), 400);
            }, 4000);
        }

        async function performAction(url, btnId, spinnerId, iconId) {
            const btn = document.getElementById(btnId);
            const spinner = document.getElementById(spinnerId);
            const icon = document.getElementById(iconId);
            const passcode = passInput ? passInput.value : '';

            // Disable buttons and show spinner
            document.querySelectorAll('.btn').forEach(b => b.disabled = true);
            spinner.style.display = 'block';
            icon.style.display = 'none';

            try {
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Web-Password': passcode
                    },
                    body: JSON.stringify({ password: passcode })
                });

                const data = await response.json();
                if (response.ok) {
                    showToast(data.message || 'Action executed successfully!', 'success');
                    setTimeout(() => window.location.reload(), 1500);
                } else {
                    showToast(data.error || 'Request failed.', 'error');
                }
            } catch (err) {
                showToast('Network error or server is offline.', 'error');
                console.error(err);
            } finally {
                document.querySelectorAll('.btn').forEach(b => b.disabled = false);
                spinner.style.display = 'none';
                icon.style.display = 'block';
            }
        }

        function triggerSync() {
            performAction('/api/sync', 'btn-sync', 'spinner-sync', 'icon-sync');
        }

        function triggerRetry() {
            performAction('/api/retry', 'btn-retry', 'spinner-retry', 'icon-retry');
        }
    </script>
</body>
</html>"""


def check_authorization():
    """Verify web password if configured."""
    if not WEB_PASSWORD:
        return True
    
    # Check headers
    provided_password = request.headers.get("X-Web-Password")
    if provided_password == WEB_PASSWORD:
        return True
        
    # Check json body
    if request.is_json:
        try:
            body = request.get_json()
            if body and body.get("password") == WEB_PASSWORD:
                return True
        except Exception:
            pass
            
    # Check query params
    if request.args.get("password") == WEB_PASSWORD:
        return True
        
    return False


@app.route("/")
def home():
    stats = uploads_db.get_stats()
    mappings = mappings_db.get_all_enabled()
    return render_template_string(
        DASHBOARD_TEMPLATE, 
        stats=stats, 
        mappings=mappings, 
        has_password=bool(WEB_PASSWORD)
    )


@app.route("/api/sync", methods=["POST"])
def api_sync():
    global monitor, loop
    if not check_authorization():
        return {"error": "Unauthorized: Invalid password"}, 401
        
    if not monitor or not loop:
        return {"error": "Sync monitor is not initialized yet. Please try again later."}, 503
        
    try:
        future = asyncio.run_coroutine_threadsafe(monitor.trigger_sync(), loop)
        future.result(timeout=15)
        return {"success": True, "message": "Manual sync completed successfully."}, 200
    except Exception as e:
        LOGGER.error(f"Failed to trigger manual sync: {e}")
        return {"error": f"Failed to trigger sync: {str(e)}"}, 500


@app.route("/api/retry", methods=["POST"])
def api_retry():
    global monitor, loop
    if not check_authorization():
        return {"error": "Unauthorized: Invalid password"}, 401
        
    if not monitor or not loop:
        return {"error": "Sync monitor is not initialized yet. Please try again later."}, 503
        
    try:
        future = asyncio.run_coroutine_threadsafe(monitor.enqueue_retryable(), loop)
        count = future.result(timeout=15)
        return {"success": True, "message": f"Successfully re-queued {count} failed upload(s).", "count": count}, 200
    except Exception as e:
        LOGGER.error(f"Failed to trigger manual retry: {e}")
        return {"error": f"Failed to trigger retry: {str(e)}"}, 500


@app.route("/health")
def health():
    return {"status": "ok"}, 200


@app.route("/oauth2callback")
def oauth2callback():
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return render_template_string("""
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
                    <h2 style="color: red;">Authorization Failed</h2>
                    <p>Error: {{ error }}</p>
                </body>
            </html>
        """, error=error), 400

    if code:
        return render_template_string("""
            <html>
                <body style="font-family: Arial, sans-serif; text-align: center; margin-top: 50px;">
                    <h2 style="color: green;">Authorization Successful!</h2>
                    <p>Please copy the code below and send it to the bot in Telegram:</p>
                    <code style="background: #f4f4f4; padding: 10px; display: inline-block; font-size: 16px; border: 1px solid #ccc;">{{ code }}</code>
                </body>
            </html>
        """, code=code)

    return "No code received.", 400


def _run():
    port = int(os.environ.get("PORT", 8080))
    LOGGER.info(f"Flask server starting on port {port}")
    app.run(host="0.0.0.0", port=port)


def start_server():
    Thread(target=_run, daemon=True).start()
