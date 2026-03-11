import logging
import uuid
from datetime import datetime, timezone
from database.db import get_db
from config import Config

logger = logging.getLogger(__name__)


def short_id():
    return uuid.uuid4().hex[:8]


# ─── USERS ────────────────────────────────────────────────────────────────────

async def add_user(user_id: int, name: str, username: str = None):
    try:
        db = get_db()
        existing = await db.users.find_one({"_id": user_id})
        if not existing:
            await db.users.insert_one({
                "_id": user_id,
                "name": name,
                "username": username,
                "joined": datetime.now(timezone.utc),
                "banned": False
            })
    except Exception as e:
        logger.error(f"add_user error: {e}")


async def get_user(user_id: int):
    try:
        db = get_db()
        return await db.users.find_one({"_id": user_id})
    except Exception as e:
        logger.error(f"get_user error: {e}")
        return None


async def is_banned(user_id: int) -> bool:
    user = await get_user(user_id)
    return bool(user and user.get("banned", False))


async def ban_user(user_id: int):
    try:
        db = get_db()
        await db.users.update_one({"_id": user_id}, {"$set": {"banned": True}}, upsert=True)
    except Exception as e:
        logger.error(f"ban_user error: {e}")


async def unban_user(user_id: int):
    try:
        db = get_db()
        await db.users.update_one({"_id": user_id}, {"$set": {"banned": False}})
    except Exception as e:
        logger.error(f"unban_user error: {e}")


async def get_all_users():
    try:
        db = get_db()
        cursor = db.users.find({"banned": False}, {"_id": 1})
        return [doc["_id"] async for doc in cursor]
    except Exception as e:
        logger.error(f"get_all_users error: {e}")
        return []


async def get_total_users() -> int:
    try:
        db = get_db()
        return await db.users.count_documents({})
    except Exception as e:
        logger.error(f"get_total_users error: {e}")
        return 0


async def get_recent_users(limit: int = 20):
    try:
        db = get_db()
        cursor = db.users.find({}).sort("joined", -1).limit(limit)
        return [doc async for doc in cursor]
    except Exception as e:
        logger.error(f"get_recent_users error: {e}")
        return []


# ─── FILES ────────────────────────────────────────────────────────────────────

async def save_file(file_id: str, file_type: str, file_name: str,
                    file_size: int, caption: str, message_id: int, uploaded_by: int) -> str:
    try:
        db = get_db()
        uid = short_id()
        await db.files.insert_one({
            "_id": uid,
            "file_id": file_id,
            "file_type": file_type,
            "file_name": file_name,
            "file_size": file_size,
            "caption": caption,
            "message_id": message_id,
            "uploaded_by": uploaded_by,
            "uploaded_at": datetime.now(timezone.utc),
            "download_count": 0
        })
        return uid
    except Exception as e:
        logger.error(f"save_file error: {e}")
        return None


async def get_file(file_uid: str):
    try:
        db = get_db()
        return await db.files.find_one({"_id": file_uid})
    except Exception as e:
        logger.error(f"get_file error: {e}")
        return None


async def increment_download(file_uid: str):
    try:
        db = get_db()
        await db.files.update_one({"_id": file_uid}, {"$inc": {"download_count": 1}})
    except Exception as e:
        logger.error(f"increment_download error: {e}")


async def delete_file(file_uid: str):
    try:
        db = get_db()
        await db.files.delete_one({"_id": file_uid})
    except Exception as e:
        logger.error(f"delete_file error: {e}")


async def get_total_files() -> int:
    try:
        db = get_db()
        return await db.files.count_documents({})
    except Exception as e:
        logger.error(f"get_total_files error: {e}")
        return 0


async def get_files_today() -> int:
    try:
        db = get_db()
        today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        return await db.files.count_documents({"uploaded_at": {"$gte": today}})
    except Exception as e:
        logger.error(f"get_files_today error: {e}")
        return 0


# ─── BATCHES ──────────────────────────────────────────────────────────────────

async def save_batch(name: str, file_ids: list, created_by: int) -> str:
    try:
        db = get_db()
        uid = short_id()
        await db.batches.insert_one({
            "_id": uid,
            "name": name,
            "files": file_ids,
            "created_by": created_by,
            "created_at": datetime.now(timezone.utc),
            "is_active": True
        })
        return uid
    except Exception as e:
        logger.error(f"save_batch error: {e}")
        return None


async def get_batch(batch_id: str):
    try:
        db = get_db()
        return await db.batches.find_one({"_id": batch_id})
    except Exception as e:
        logger.error(f"get_batch error: {e}")
        return None


async def get_total_batches() -> int:
    try:
        db = get_db()
        return await db.batches.count_documents({})
    except Exception as e:
        logger.error(f"get_total_batches error: {e}")
        return 0


# ─── ADMINS ───────────────────────────────────────────────────────────────────

async def add_admin(user_id: int, name: str, added_by: int):
    try:
        db = get_db()
        await db.admins.update_one(
            {"_id": user_id},
            {"$set": {"name": name, "added_by": added_by, "added_at": datetime.now(timezone.utc)}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"add_admin error: {e}")


async def remove_admin(user_id: int):
    try:
        db = get_db()
        await db.admins.delete_one({"_id": user_id})
    except Exception as e:
        logger.error(f"remove_admin error: {e}")


async def get_all_admins():
    try:
        db = get_db()
        cursor = db.admins.find({})
        return [doc async for doc in cursor]
    except Exception as e:
        logger.error(f"get_all_admins error: {e}")
        return []


async def is_admin_in_db(user_id: int) -> bool:
    try:
        db = get_db()
        doc = await db.admins.find_one({"_id": user_id})
        return doc is not None
    except Exception as e:
        logger.error(f"is_admin_in_db error: {e}")
        return False


# ─── SETTINGS ─────────────────────────────────────────────────────────────────

DEFAULT_SETTINGS = {
    "_id": "bot_settings",
    "force_sub_channels": [],
    "force_sub_enabled": False,
    "welcome_message": "👋 Hello {first_name}!\n\nWelcome to <b>{bot_name}</b>!\nSend or receive files with ease.",
    "auto_delete_enabled": False,
    "auto_delete_seconds": 600,
    "protect_content": False,
    "bot_maintenance": False,
    "join_request_mode": False
}


async def get_settings() -> dict:
    try:
        db = get_db()
        settings = await db.settings.find_one({"_id": "bot_settings"})
        if not settings:
            await db.settings.insert_one(DEFAULT_SETTINGS.copy())
            return DEFAULT_SETTINGS.copy()
        return settings
    except Exception as e:
        logger.error(f"get_settings error: {e}")
        return DEFAULT_SETTINGS.copy()


async def update_settings(update: dict):
    try:
        db = get_db()
        await db.settings.update_one(
            {"_id": "bot_settings"},
            {"$set": update},
            upsert=True
        )
    except Exception as e:
        logger.error(f"update_settings error: {e}")
