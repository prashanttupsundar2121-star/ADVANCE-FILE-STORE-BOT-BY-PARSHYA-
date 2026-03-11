import logging
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

logger = logging.getLogger(__name__)

client = None
db = None

async def connect_db():
    global client, db
    try:
        client = AsyncIOMotorClient(Config.MONGO_URI)
        db = client["filestorebot"]
        await client.admin.command("ping")
        logger.info("✅ MongoDB connected successfully!")
        return db
    except Exception as e:
        logger.error(f"❌ MongoDB connection failed: {e}")
        raise

def get_db():
    return db
