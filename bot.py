import asyncio
import logging
import logging.handlers
import os
from pyrogram import Client, idle
from database.db import connect_db
from database.models import add_admin, get_all_admins, get_settings
from utils.filters import update_admin_cache
from config import Config

# ─── LOGGING ──────────────────────────────────────────────────────────────────
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

logging.basicConfig(
    level=logging.INFO,
    format=LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.handlers.RotatingFileHandler(
            "bot.log", maxBytes=5 * 1024 * 1024, backupCount=3
        )
    ]
)
logger = logging.getLogger(__name__)

# ─── CLIENT ───────────────────────────────────────────────────────────────────
app = Client(
    "AdvancedFileStoreBot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins"),
    sleep_threshold=60
)


async def load_admins():
    """Seed admins from config into DB and load into cache."""
    for uid in Config.ADMINS:
        await add_admin(uid, str(uid), Config.OWNER_ID)
    db_admins = await get_all_admins()
    all_ids = [a["_id"] for a in db_admins] + [Config.OWNER_ID]
    update_admin_cache(all_ids)
    logger.info(f"✅ Loaded {len(all_ids)} admins into cache.")


async def periodic_admin_reload():
    """Reload admin cache from DB every 30 minutes."""
    while True:
        await asyncio.sleep(1800)
        try:
            db_admins = await get_all_admins()
            all_ids = [a["_id"] for a in db_admins] + [Config.OWNER_ID]
            update_admin_cache(all_ids)
            logger.info("🔄 Admin cache refreshed.")
        except Exception as e:
            logger.error(f"periodic_admin_reload error: {e}")


async def main():
    logger.info("🚀 Starting Advanced File Store Bot...")

    # Connect to MongoDB
    await connect_db()

    # Load admins
    await load_admins()

    # Start bot
    await app.start()
    bot_info = await app.get_me()
    logger.info(f"✅ Bot started as @{bot_info.username}")

    # Notify owner
    try:
        await app.send_message(
            Config.OWNER_ID,
            f"✅ <b>{Config.BOT_NAME} is online!</b>\n\n"
            f"🤖 @{bot_info.username}\n"
            f"👥 Admins loaded: {len(await get_all_admins())}",
            parse_mode="html"
        )
    except Exception:
        pass

    # Start background tasks
    asyncio.create_task(periodic_admin_reload())

    await idle()
    await app.stop()
    logger.info("🛑 Bot stopped.")


if __name__ == "__main__":
    asyncio.run(main())
