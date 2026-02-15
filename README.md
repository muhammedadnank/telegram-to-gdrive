# 🎵 Music to Google Drive — Telegram Bot

A clean, secure, lightweight Telegram bot to upload **music and audio files** directly to your **Google Drive** — powered by Python, Pyrogram, and MongoDB.

![Python](https://img.shields.io/badge/Python-3.10+-blue?style=flat-square&logo=python)
![MongoDB](https://img.shields.io/badge/Database-MongoDB-green?style=flat-square&logo=mongodb)
![License](https://img.shields.io/badge/License-GPLv3-yellow?style=flat-square)
![Deploy](https://img.shields.io/badge/Deploy-Render-purple?style=flat-square&logo=render)

---

## ✨ Features

- 🎵 Upload audio files (mp3, flac, wav, m4a, ogg, etc.) from Telegram to Google Drive
- 🔐 Secure OAuth2 Google Drive authentication — per user
- 🛡️ Safe credential storage using JSON (no pickle / no RCE risk)
- 📁 Custom upload folder support
- 🗄️ MongoDB Atlas database (free tier supported)
- ☁️ Deploy-ready for [Render](https://render.com)

---

## 🚀 Deploying on Render

### Step 1 — Fork this Repository

Click **Fork** on GitHub to create your own copy.

### Step 2 — Create a Render Web Service

1. Go to [render.com](https://render.com) and sign in with GitHub
2. Click **New +** → **Web Service**
3. Select your forked repository
4. Set the following:

| Field | Value |
|-------|-------|
| Environment | `Python` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python3 -m bot` |

### Step 3 — Set Environment Variables

Add these in the **Environment** tab on Render:

| Variable | Description |
|----------|-------------|
| `BOT_TOKEN` | Get from [@BotFather](https://t.me/botfather) |
| `APP_ID` | Get from [my.telegram.org](https://my.telegram.org/apps) |
| `API_HASH` | Get from [my.telegram.org](https://my.telegram.org/apps) |
| `MONGO_URI` | MongoDB Atlas connection string |
| `SUDO_USERS` | Your Telegram User ID (space-separated for multiple) |
| `G_DRIVE_CLIENT_ID` | Google OAuth2 Client ID |
| `G_DRIVE_CLIENT_SECRET` | Google OAuth2 Client Secret |
| `DOWNLOAD_DIRECTORY` | *(Optional)* Default: `./downloads/` |

---

## 🗄️ MongoDB Setup (Free)

1. Go to [mongodb.com/atlas](https://www.mongodb.com/atlas) and create a free account
2. Create a **free M0 cluster** (AWS, Mumbai region recommended)
3. Under **Database Access** → Add a new user with a password
4. Under **Network Access** → Allow access from anywhere (`0.0.0.0/0`)
5. Click **Connect** → **Drivers** → Copy the connection string

Your `MONGO_URI` will look like:
```
mongodb+srv://username:password@cluster.xxxxx.mongodb.net/?retryWrites=true&w=majority
```

> ✅ No need to create collections manually — the bot creates them automatically on first run.

---

## 🔑 Google Drive Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable the **Google Drive API**
4. Go to **Credentials** → **Create Credentials** → **OAuth 2.0 Client ID**
5. Choose **Desktop app** as the application type
6. Copy the **Client ID** and **Client Secret** into your environment variables

---

## 🤖 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show help |
| `/auth` | Authenticate your Google Drive account |
| `/revoke` | Revoke current Google Drive account |
| `/setfolder <folder_url>` | Set a custom upload folder |

---

## 📦 Local Installation

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/telegram-to-gdrive
cd telegram-to-gdrive

# Install dependencies
pip3 install -r requirements.txt

# Copy and fill in your environment variables
cp .env.sample .env
nano .env

# Run the bot
python3 -m bot
```

---

## 🛡️ Security

This project follows secure coding practices:

- ✅ No `pickle` usage — credentials stored as JSON using `oauth2client`'s built-in methods
- ✅ No hardcoded secrets or API keys
- ✅ No third-party OAuth redirect dependencies
- ✅ All sensitive config loaded from environment variables only

---

## 🛠️ Tech Stack

| Library | Purpose |
|---------|---------|
| [Pyrofork](https://github.com/Mayuri-Chan/pyrofork) | Telegram MTProto client |
| [PyMongo](https://pymongo.readthedocs.io/) | MongoDB driver |
| [oauth2client](https://github.com/googleapis/oauth2client) | Google OAuth2 |
| [Google API Python Client](https://github.com/googleapis/google-api-python-client) | Google Drive API |
| [Flask](https://flask.palletsprojects.com/) + [Gunicorn](https://gunicorn.org/) | Keep-alive web server for Render |

---

## 📜 Credits

- [Dan](https://github.com/delivrance) for [Pyrogram](https://pyrogram.org)
- [Spechide](https://github.com/Spechide) for the original database helper
- [Shivam Jha](https://github.com/lzzy12) for GDrive utils from [python-aria-mirror-bot](https://github.com/lzzy12/python-aria-mirror-bot)
- [Adnan Ahmad](https://github.com/viperadnan-git) — Original project author

---

## 📄 License

Licensed under the [GNU General Public License v3.0](./LICENSE)
