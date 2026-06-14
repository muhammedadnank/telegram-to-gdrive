import re
from pyrogram import Client, filters
from pyrogram.types import Message

from bot import SUDO_USERS, LOGGER
from bot.helpers.db import mappings as mappings_db
from bot.helpers.db import uploads as uploads_db
from bot.helpers.db import tokens as tokens_db

# Access the monitor via app state (set in __main__.py)
def _monitor(client):
    return getattr(client, "_drive_monitor", None)


def _is_admin(message: Message) -> bool:
    return message.from_user.id in SUDO_USERS


# ─── /addfolder <folder_url_or_id> <channel_id> ──────────────────────────────

@Client.on_message(filters.private & filters.command("addfolder"))
async def cmd_addfolder(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    parts = message.command[1:]
    if len(parts) < 2:
        return await message.reply_text(
            "**Usage:** `/addfolder <folder_url_or_id> <channel_id>`", quote=True
        )

    raw_folder, channel_id = parts[0], parts[1]

    # Extract folder ID from URL if needed
    match = re.search(r"folders/([a-zA-Z0-9_-]+)", raw_folder)
    folder_id = match.group(1) if match else raw_folder

    if not channel_id.lstrip("-").isdigit():
        return await message.reply_text("❗ Channel ID must be a number (e.g. `-100123456789`).", quote=True)

    ok = mappings_db.add(folder_id, channel_id)
    if ok:
        LOGGER.info(f"Admin {message.from_user.id} added folder {folder_id} → {channel_id}")
        await message.reply_text(
            f"✅ **Folder mapped successfully.**\n"
            f"**Folder ID:** `{folder_id}`\n"
            f"**Channel:** `{channel_id}`",
            quote=True,
        )
    else:
        await message.reply_text("❗ Failed to save mapping. Check logs.", quote=True)


# ─── /removefolder <folder_id> ───────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("removefolder"))
async def cmd_removefolder(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    parts = message.command[1:]
    if not parts:
        return await message.reply_text("**Usage:** `/removefolder <folder_id>`", quote=True)

    folder_id = parts[0]
    ok = mappings_db.remove(folder_id)
    tokens_db.delete(folder_id)

    if ok:
        LOGGER.info(f"Admin {message.from_user.id} removed folder {folder_id}")
        await message.reply_text(f"✅ **Mapping disabled.**\n`{folder_id}`", quote=True)
    else:
        await message.reply_text("❗ No active mapping found for that folder ID.", quote=True)


# ─── /status ─────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("status"))
async def cmd_status(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    monitor = _monitor(client)
    running = "✅ Running" if (monitor and monitor._running) else "❌ Stopped"
    q_size = monitor._queue.qsize() if monitor else "—"

    mappings = mappings_db.get_all_enabled()
    if mappings:
        lines = "\n".join(
            f"  `{m['folder_id']}` → `{m['channel_id']}`" for m in mappings
        )
    else:
        lines = "  _No active mappings_"

    await message.reply_text(
        f"**🤖 Bot Status**\n\n"
        f"**Monitor:** {running}\n"
        f"**Queue size:** {q_size}\n\n"
        f"**Active Folder Mappings:**\n{lines}",
        quote=True,
    )


# ─── /stats ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("stats"))
async def cmd_stats(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    s = uploads_db.get_stats()
    await message.reply_text(
        f"**📊 Upload Stats**\n\n"
        f"✅ Completed: **{s.get('completed', 0)}**\n"
        f"⏳ Pending/Active: **{s.get('pending', 0)}**\n"
        f"❌ Failed: **{s.get('failed', 0)}**\n"
        f"📁 Total records: **{s.get('total', 0)}**",
        quote=True,
    )


# ─── /last ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("last"))
async def cmd_last(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    doc = uploads_db.get_last_completed()
    if not doc:
        return await message.reply_text("No completed uploads yet.", quote=True)

    uploaded_at = doc.get("uploaded_at")
    time_str = uploaded_at.strftime("%Y-%m-%d %H:%M UTC") if uploaded_at else "—"

    await message.reply_text(
        f"**🎵 Last Uploaded File**\n\n"
        f"**Name:** `{doc.get('file_name')}`\n"
        f"**Drive ID:** `{doc.get('file_id')}`\n"
        f"**Channel:** `{doc.get('channel_id')}`\n"
        f"**Uploaded at:** {time_str}",
        quote=True,
    )


# ─── /sync ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("sync"))
async def cmd_sync(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    monitor = _monitor(client)
    if not monitor:
        return await message.reply_text("❗ Monitor not initialized.", quote=True)

    await message.reply_text("🔄 **Manual sync started...**", quote=True)
    await monitor.trigger_sync()
    await message.reply_text("✅ **Sync complete.** New files (if any) added to queue.", quote=True)


# ─── /retry ──────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("retry"))
async def cmd_retry(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    monitor = _monitor(client)
    if not monitor:
        return await message.reply_text("❗ Monitor not initialized.", quote=True)

    count = await monitor.enqueue_retryable()
    if count:
        await message.reply_text(f"♻️ **Re-queued {count} failed upload(s).**", quote=True)
    else:
        await message.reply_text("✅ No retryable failed uploads found.", quote=True)


# ─── /logs ───────────────────────────────────────────────────────────────────

@Client.on_message(filters.private & filters.command("logs"))
async def cmd_logs(client: Client, message: Message):
    if not _is_admin(message):
        return await message.reply_text("🚫 **Admin only.**", quote=True)

    try:
        with open("log.txt", "rb") as f:
            await client.send_document(
                message.chat.id,
                document=f,
                file_name="log.txt",
                reply_to_message_id=message.id,
            )
    except Exception as e:
        await message.reply_text(f"❗ Could not send log: `{e}`", quote=True)
