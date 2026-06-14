# 🎵 Google Drive ⇆ Telegram Music Bot

A premium, reliable, and highly automated dual-sync Telegram bot that supports:
1. **Google Drive ➔ Telegram Sync**: Automatically syncs audio files from mapped Google Drive folders to Telegram channels (using the administrator's OAuth2 account).
2. **Telegram ➔ Google Drive Upload**: Authenticated users can send audio files directly to the bot to upload to their personal Google Drives (using OAuth2).

Powered by Python, Pyrofork (Pyrogram), and MongoDB.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-green?style=flat-square&logo=mongodb)
![License](https://img.shields.io/badge/License-GPLv3-yellow?style=flat-square)
![Deploy](https://img.shields.io/badge/Deploy-Render-purple?style=flat-square&logo=render)

---

## ✨ Features

- 🔄 **Google Drive ➔ Telegram Sync**:
  - **Delta Polling**: Queries Drive changes via the Google Drive `changes.list` API, resuming exactly where it left off.
  - **State Persistence**: Mappings, page tokens, and upload logs are saved in MongoDB Atlas.
  - **Concurrent Queue**: Downloads and posts files using an asynchronous worker queue.
  - **Bandwidth-Efficient Retries**: Reuses locally cached files in the `failed/` directory when retrying, preventing duplicate downloads.
  - **Self-Healing**: Handles expired/invalid start tokens by automatically resetting to a fresh token state.

- 📤 **Telegram ➔ Google Drive Upload**:
  - **OAuth2 Authorization**: Users can link their Google accounts via `/auth` with a web callback page.
  - **Custom Folders**: Set custom parent folders using `/setfolder <folder_url>`.
  - **Selective Uploads**: Only processes audio MIME types (MP3, FLAC, M4A, WAV, etc.) to keep the Drive organized.

---

## 🏗️ Architecture Flow

```
1️⃣ Google Drive ➔ Telegram Sync
   Google Drive (OAuth2 Account) ➔ changes.list Poll ➔ Worker Queue (Concurrently) ➔ Telegram Channel

2️⃣ Telegram ➔ Google Drive Upload
   Telegram User ➔ Sent Audio File ➔ OAuth2 Validation (gDriveDB) ➔ Uploaded to Custom Parent Folder
```

---

## 🚀 Deployment (Render)

### Step 1 — Fork this Repository
Click **Fork** on GitHub to create your own copy of the repository.

### Step 2 — Create a Render Web Service
1. Go to [render.com](https://render.com) and create a **Web Service**.
2. Connect your forked repository.
3. Configure:
   - **Runtime**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python3 -m bot`

### Step 3 — Environment Variables

| Variable | Description | Required / Optional |
|---|---|---|
| `BOT_TOKEN` | Get from [@BotFather](https://t.me/botfather) | **Required** |
| `APP_ID` | Get from [my.telegram.org](https://my.telegram.org) | **Required** |
| `API_HASH` | Get from [my.telegram.org](https://my.telegram.org) | **Required** |
| `MONGO_URI` | MongoDB Atlas Connection String | **Required** |
| `SUDO_USERS` | Space-separated Telegram User IDs of Admins | **Required** |
| `G_DRIVE_CLIENT_ID` | Google Client ID for OAuth access | **Required** |
| `G_DRIVE_CLIENT_SECRET` | Google Client Secret for OAuth access | **Required** |
| `REDIRECT_URI` | Web callback URL for OAuth (e.g. `https://app.onrender.com/oauth2callback`) | *Optional* |
| `MAX_WORKERS` | Max concurrent worker tasks (default: `3`) | *Optional* |
| `POLL_INTERVAL` | Interval in seconds between checks (default: `45`) | *Optional* |
| `DOWNLOAD_DIRECTORY` | Active downloads folder path | *Optional* |
| `FAILED_DIRECTORY` | Failed files directory for retries | *Optional* |
| `WEB_PASSWORD` | Security password for accessing the dashboard API/actions | *Optional* |


---

## 🔑 Setup Guides

### 1. Google OAuth 2.0 Credentials (Needed for All Features)
1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a project and enable the **Google Drive API**.
3. Configure the **OAuth consent screen** (External, add test users including admin emails).
4. Go to **Credentials** ➔ **Create Credentials** ➔ **OAuth client ID**.
5. Select application type **Web application**.
6. Add your redirect URI to **Authorized redirect URIs** (e.g., `https://your-bot-url.onrender.com/oauth2callback`).
7. Copy the client ID and client secret, then set `G_DRIVE_CLIENT_ID`, `G_DRIVE_CLIENT_SECRET`, and `REDIRECT_URI` in the environment.
8. Admin/Sudo users must run `/auth` in the bot to link their Google Drive accounts before adding any folder mappings.

### 2. MongoDB Setup
1. Create a free cluster on [mongodb.com](https://www.mongodb.com).
2. Add a database user with read/write access.
3. Allow connections from anywhere (`0.0.0.0/0`).
4. Copy the connection string and set `MONGO_URI`.

---

## 🤖 Bot Commands

### Admin Commands (Sudo/Admins only)
| Command | Arguments | Description |
|---|---|---|
| `/addfolder` | `<folder_url/id> <channel_id>` | Maps a Google Drive folder to a Telegram Channel |
| `/removefolder`| `<folder_id>` | Removes a folder-channel mapping |
| `/status` | None | Displays current worker state, mappings, and queue size |
| `/stats` | None | Shows upload statistics (total, pending, failed) |
| `/last` | None | Shows details of the last successfully sync-uploaded file |
| `/sync` | None | Triggers an immediate manual check of Drive changes |
| `/retry` | None | Re-queues failed items for synchronization |
| `/logs` | None | Sends the current `log.txt` log file |

### User Commands (All Users)
| Command | Arguments | Description |
|---|---|---|
| `/auth` | None | Initiates personal Google Drive account authorization |
| `/revoke` | None | Revokes authorized Google Drive account access |
| `/setfolder` | `<folder_url/id>` | Sets custom folder for your Telegram uploads (or `/setfolder clear`) |
| `/help` | None | Shows help documentation and active commands |

---

## 📦 Local Installation

```bash
# Clone the repository
git clone https://github.com/muhammedadnank/telegram-to-gdrive
cd telegram-to-gdrive

# Install dependencies
pip3 install -r requirements.txt

# Copy and configure environment variables
cp .env.sample .env
nano .env

# Run the bot
python3 -m bot
```

---

## 🛠️ Tech Stack

- **Pyrofork**: High-performance Telegram MTProto client.
- **PyMongo**: MongoDB driver for Python.
- **Google API Python Client**: Native Google Drive API client.
- **Flask**: Web callback and health-check server.
- **Tenacity**: Retry handlers for resilient network calls.

---

## 📜 Credits

- [Dan](https://github.com/delivrance) for [Pyrogram](https://pyrogram.org)
- [Spechide](https://github.com/Spechide) for database helpers
- [Shivam Jha](https://github.com/lzzy12) for GDrive utils from [python-aria-mirror-bot](https://github.com/lzzy12/python-aria-mirror-bot)
- [Adnan Ahmad](https://github.com/viperadnan-git) — Original project author

---

## 📄 License

Licensed under the [GNU General Public License v3.0](./LICENSE)
