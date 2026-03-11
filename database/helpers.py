import logging
import asyncio
from datetime import datetime, timezone
from pyrogram import Client
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, ChannelInvalid, FloodWait
from database.models import get_settings
from config import Config

logger = logging.getLogger(__name__)

BOT_START_TIME = datetime.now(timezone.utc)


def get_uptime() -> str:
    delta = datetime.now(timezone.utc) - BOT_START_TIME
    days = delta.days
    hours, rem = divmod(delta.seconds, 3600)
    minutes, _ = divmod(rem, 60)
    return f"{days}d {hours}h {minutes}m"


def human_size(size: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"


async def check_force_sub(client: Client, user_id: int) -> list:
    """Returns list of channels user hasn't joined. Empty list = all joined."""
    settings = await get_settings()
    if not settings.get("force_sub_enabled", False):
        return []

    channels = settings.get("force_sub_channels", [])
    not_joined = []

    for ch in channels:
        if not ch:
            continue
        try:
            member = await client.get_chat_member(ch, user_id)
            if member.status.name in ("BANNED", "LEFT"):
                not_joined.append(ch)
        except UserNotParticipant:
            not_joined.append(ch)
        except (ChatAdminRequired, ChannelInvalid):
            logger.warning(f"Bot not admin or channel invalid: {ch}")
        except Exception as e:
            logger.error(f"check_force_sub error for {ch}: {e}")

    return not_joined


async def get_file_info(message):
    """Extract file info from a Pyrogram message."""
    if message.document:
        f = message.document
        return f.file_id, "document", f.file_name or "Document", f.file_size
    elif message.video:
        f = message.video
        return f.file_id, "video", f.file_name or "Video.mp4", f.file_size
    elif message.audio:
        f = message.audio
        return f.file_id, "audio", f.file_name or "Audio.mp3", f.file_size
    elif message.photo:
        f = message.photo
        return f.file_id, "photo", "Photo.jpg", f.file_size
    elif message.voice:
        f = message.voice
        return f.file_id, "voice", "Voice.ogg", f.file_size
    elif message.video_note:
        f = message.video_note
        return f.file_id, "video_note", "VideoNote.mp4", f.file_size
    elif message.sticker:
        f = message.sticker
        return f.file_id, "sticker", f.file_name or "Sticker.webp", f.file_size
    elif message.animation:
        f = message.animation
        return f.file_id, "animation", f.file_name or "Animation.gif", f.file_size
    return None, None, None, 0


async def send_file_to_user(client: Client, chat_id: int, message_id: int, protect: bool = False):
    """Copy a file from LOG_CHANNEL to the user."""
    try:
        await client.copy_message(
            chat_id=chat_id,
            from_chat_id=Config.LOG_CHANNEL,
            message_id=message_id,
            protect_content=protect
        )
        return True
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_file_to_user(client, chat_id, message_id, protect)
    except Exception as e:
        logger.error(f"send_file_to_user error: {e}")
        return False
