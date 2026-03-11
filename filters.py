import logging
from pyrogram import filters
from config import Config

logger = logging.getLogger(__name__)

# In-memory admin cache — populated on startup and refreshed periodically
admin_cache: set = set(Config.ADMINS)


def update_admin_cache(admin_ids: list):
    global admin_cache
    admin_cache = set(admin_ids)
    admin_cache.add(Config.OWNER_ID)


async def _is_admin(_, __, message):
    try:
        user_id = message.from_user.id if message.from_user else None
        if not user_id:
            return False
        return user_id in admin_cache or user_id == Config.OWNER_ID
    except Exception as e:
        logger.error(f"admin filter error: {e}")
        return False


async def _is_owner(_, __, message):
    try:
        user_id = message.from_user.id if message.from_user else None
        return user_id == Config.OWNER_ID
    except Exception:
        return False


admin_filter = filters.create(_is_admin, name="AdminFilter")
owner_filter = filters.create(_is_owner, name="OwnerFilter")
