import os
import asyncio
import logging
from pathlib import Path

from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from googleapiclient.errors import HttpError
from pyrogram.errors import FloodWait

from bot import (
    LOGGER,
    SUDO_USERS,
    MAX_WORKERS,
    POLL_INTERVAL,
    DOWNLOAD_DIRECTORY,
    FAILED_DIRECTORY,
)
from bot.helpers.db import mappings as mappings_db
from bot.helpers.db import tokens as tokens_db
from bot.helpers.db import uploads as uploads_db
from bot.helpers.db import gDriveDB

AUDIO_EXTS = {".mp3", ".m4a", ".flac", ".wav", ".aac", ".ogg", ".opus"}
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


class DriveMonitor:
    def __init__(self, pyrogram_client):
        self._client = pyrogram_client
        self._queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._workers: list[asyncio.Task] = []
        self._loop = asyncio.get_event_loop()

    # ─── Public ─────────────────────────────────────────────────────────────

    async def start(self):
        self._running = True
        for _ in range(MAX_WORKERS):
            t = asyncio.create_task(self._worker())
            self._workers.append(t)
        asyncio.create_task(self._poll_loop())
        LOGGER.info(f"DriveMonitor started ({MAX_WORKERS} workers, {POLL_INTERVAL}s interval)")

    async def stop(self):
        self._running = False
        for t in self._workers:
            t.cancel()
        LOGGER.info("DriveMonitor stopped.")

    async def trigger_sync(self):
        """Force an immediate poll of all mapped folders."""
        LOGGER.info("Manual sync triggered.")
        await self._check_all_folders()

    async def enqueue_retryable(self):
        """Re-queue all failed records with retry_count < 3."""
        items = uploads_db.get_retryable()
        count = 0
        for item in items:
            uploads_db.reset_for_retry(item["file_id"])
            mapping = mappings_db.get(item["folder_id"])
            added_by = mapping.get("added_by") if mapping else None
            await self._queue.put(
                {
                    "file_id": item["file_id"],
                    "file_name": item["file_name"],
                    "folder_id": item["folder_id"],
                    "channel_id": item["channel_id"],
                    "from_failed": True,
                    "added_by": added_by,
                }
            )
            count += 1
        LOGGER.info(f"Re-queued {count} retryable item(s).")
        return count

    # ─── Poll Loop ──────────────────────────────────────────────────────────

    async def _poll_loop(self):
        while self._running:
            try:
                await self._check_all_folders()
            except Exception as e:
                LOGGER.error(f"Poll loop error: {e}")
            await asyncio.sleep(POLL_INTERVAL)

    def get_service_for_user(self, user_id=None):
        """Build and return a Google Drive service using user OAuth2 credentials."""
        if not user_id:
            return None
        creds = gDriveDB.search(user_id)
        if creds:
            try:
                from httplib2 import Http
                creds.refresh(Http())
                gDriveDB._set(user_id, creds)
                return build("drive", "v3", credentials=creds, cache_discovery=False)
            except Exception as e:
                LOGGER.warning(f"Failed to refresh OAuth credentials for user {user_id}: {e}")
        else:
            LOGGER.warning(f"No OAuth credentials found in DB for user {user_id}")
        return None



    async def _check_all_folders(self):
        folder_maps = mappings_db.get_all_enabled()
        if not folder_maps:
            return
        for mapping in folder_maps:
            await self._loop.run_in_executor(None, self._poll_folder, mapping)

    def _poll_folder(self, mapping: dict):
        folder_id = mapping["folder_id"]
        channel_id = mapping["channel_id"]
        added_by = mapping.get("added_by")

        service = self.get_service_for_user(added_by)
        if not service:
            LOGGER.error(f"Cannot poll folder {folder_id}: No valid credentials available (user: {added_by})")
            return

        token = tokens_db.get(folder_id)
        if not token:
            # First run: get start token so we don't re-upload old files
            try:
                resp = service.changes().getStartPageToken().execute()
                token = resp.get("startPageToken")
                tokens_db.set(folder_id, token)
                LOGGER.info(f"Initialized page token for folder {folder_id}")
            except Exception as e:
                LOGGER.error(f"Failed to get start page token for {folder_id}: {e}")
            return

        current_token = token
        while current_token:
            try:
                resp = (
                    service.changes()
                    .list(
                        pageToken=current_token,
                        spaces="drive",
                        fields="nextPageToken, newStartPageToken, changes(file(id, name, mimeType, parents, trashed))",
                        includeRemoved=False,
                        supportsAllDrives=True,
                        includeItemsFromAllDrives=True,
                    )
                    .execute()
                )
            except HttpError as e:
                LOGGER.error(f"changes.list HTTP error for {folder_id}: {e}")
                if e.resp.status in (400, 404):
                    LOGGER.warning(f"Page token for folder {folder_id} is expired or invalid. Resetting.")
                    tokens_db.delete(folder_id)
                return
            except Exception as e:
                LOGGER.error(f"changes.list unexpected error for {folder_id}: {e}")
                return

            changes = resp.get("changes", [])
            for change in changes:
                f = change.get("file", {})
                if f.get("trashed"):
                    continue
                parents = f.get("parents", [])
                if folder_id not in parents:
                    continue
                name = f.get("name", "")
                ext = Path(name).suffix.lower()
                if ext not in AUDIO_EXTS:
                    continue
                file_id = f["id"]
                if uploads_db.is_uploaded(file_id):
                    LOGGER.debug(f"Skip (already uploaded): {name}")
                    continue
                uploads_db.create_pending(file_id, name, folder_id, channel_id)
                self._loop.call_soon_threadsafe(
                    self._queue.put_nowait,
                    {
                        "file_id": file_id,
                        "file_name": name,
                        "folder_id": folder_id,
                        "channel_id": channel_id,
                        "from_failed": False,
                        "added_by": added_by,
                    },
                )
                LOGGER.info(f"Queued: {name} ({file_id}) → {channel_id}")

            next_page_token = resp.get("nextPageToken")
            new_start_page_token = resp.get("newStartPageToken")

            if next_page_token:
                current_token = next_page_token
                tokens_db.set(folder_id, current_token)
            elif new_start_page_token:
                if new_start_page_token != token:
                    tokens_db.set(folder_id, new_start_page_token)
                break
            else:
                break

    # ─── Worker ─────────────────────────────────────────────────────────────

    async def _worker(self):
        while True:
            task = await self._queue.get()
            try:
                await self._process(task)
            except asyncio.CancelledError:
                break
            except Exception as e:
                LOGGER.error(f"Worker unhandled error: {e}")
            finally:
                self._queue.task_done()

    async def _process(self, task: dict):
        file_id = task["file_id"]
        file_name = task["file_name"]
        folder_id = task["folder_id"]
        channel_id = task["channel_id"]
        from_failed = task.get("from_failed", False)
        added_by = task.get("added_by")

        local_path = os.path.join(DOWNLOAD_DIRECTORY, "drive", file_name)
        failed_path = os.path.join(FAILED_DIRECTORY, file_name)

        # Get service for this task
        service = self.get_service_for_user(added_by)
        if not service:
            LOGGER.error(f"Cannot process task for file {file_name}: No valid credentials available (user: {added_by})")
            await self._handle_failure(file_id, file_name, local_path, failed_path, channel_id)
            return

        # ── Download ──────────────────────────────────────────────────────
        uploads_db.set_status(file_id, "downloading")
        try:
            if from_failed and os.path.exists(failed_path):
                LOGGER.info(f"Re-using local failed file: {failed_path}")
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                os.replace(failed_path, local_path)
            else:
                await self._loop.run_in_executor(None, self._download_file, service, file_id, local_path)
        except Exception as e:
            LOGGER.error(f"Download failed [{file_name}]: {e}")
            await self._handle_failure(file_id, file_name, local_path, failed_path, channel_id)
            return

        # ── Upload to Telegram ────────────────────────────────────────────
        uploads_db.set_status(file_id, "uploading")
        try:
            folder_name = await self._get_folder_name(service, folder_id)
            caption = (
                f"**{file_name}**\n\n"
                f"📁 Source: {folder_name}\n"
                f"__Uploaded automatically from Google Drive__"
            )
            for attempt in range(3):
                try:
                    await self._client.send_audio(
                        chat_id=int(channel_id),
                        audio=local_path,
                        caption=caption,
                    )
                    break  # success
                except FloodWait as e:
                    if attempt < 2:
                        LOGGER.warning(
                            f"FloodWait ({channel_id}): waiting {e.value}s "
                            f"(attempt {attempt + 1}/3)"
                        )
                        await asyncio.sleep(e.value)
                    else:
                        LOGGER.error(f"FloodWait persisted after 3 attempts for {file_name}")
                        raise
            uploads_db.set_status(file_id, "completed")
            LOGGER.info(f"Uploaded successfully: {file_name} → {channel_id}")
        except Exception as e:
            LOGGER.error(f"Telegram upload failed [{file_name}]: {e}")
            await self._handle_failure(file_id, file_name, local_path, failed_path, channel_id)
            return
        finally:
            # Always clean up local file after attempt
            if os.path.exists(local_path):
                os.remove(local_path)

        # If it came from failed/ dir, clean that up too
        if from_failed and os.path.exists(failed_path):
            os.remove(failed_path)

    def _download_file(self, service, file_id: str, dest_path: str):
        request = service.files().get_media(fileId=file_id, supportsAllDrives=True)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as fh:
            downloader = MediaIoBaseDownload(fh, request, chunksize=8 * 1024 * 1024)
            done = False
            while not done:
                _, done = downloader.next_chunk()

    async def _get_folder_name(self, service, folder_id: str) -> str:
        try:
            meta = await self._loop.run_in_executor(
                None,
                lambda: service.files()
                .get(fileId=folder_id, fields="name", supportsAllDrives=True)
                .execute(),
            )
            return meta.get("name", folder_id)
        except Exception:
            return folder_id

    async def _handle_failure(
        self, file_id: str, file_name: str, local_path: str, failed_path: str, channel_id: str
    ):
        # Move file to failed/ if it exists
        if os.path.exists(local_path):
            os.makedirs(os.path.dirname(failed_path), exist_ok=True)
            os.replace(local_path, failed_path)

        retry_count = uploads_db.increment_retry(file_id)
        LOGGER.warning(f"Failed [{file_name}] retry_count={retry_count}")

        if retry_count >= 3:
            LOGGER.error(f"Max retries reached for {file_name} — alerting admins.")
            await self._alert_admins(file_name, file_id)

    async def _alert_admins(self, file_name: str, file_id: str):
        msg = (
            f"⚠️ **Upload abandoned after 3 retries**\n\n"
            f"**File:** `{file_name}`\n"
            f"**Drive ID:** `{file_id}`\n"
            f"__Manual intervention required.__"
        )
        for uid in SUDO_USERS:
            try:
                await self._client.send_message(uid, msg)
            except Exception as e:
                LOGGER.error(f"Could not alert admin {uid}: {e}")
