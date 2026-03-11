import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    API_ID = int(os.environ.get("API_ID", 0))
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
    OWNER_ID = int(os.environ.get("OWNER_ID", 0))
    MONGO_URI = os.environ.get("MONGO_URI", "")
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", 0))
    BOT_NAME = os.environ.get("BOT_NAME", "File Store Bot")
    FORCE_SUB_CHANNEL_1 = int(os.environ.get("FORCE_SUB_CHANNEL_1", 0))
    FORCE_SUB_CHANNEL_2 = int(os.environ.get("FORCE_SUB_CHANNEL_2", 0))
    FORCE_SUB_CHANNEL_3 = int(os.environ.get("FORCE_SUB_CHANNEL_3", 0))

    _admins_raw = os.environ.get("ADMINS", "")
    ADMINS = [int(x.strip()) for x in _admins_raw.split(",") if x.strip().isdigit()]
    if OWNER_ID and OWNER_ID not in ADMINS:
        ADMINS.append(OWNER_ID)
