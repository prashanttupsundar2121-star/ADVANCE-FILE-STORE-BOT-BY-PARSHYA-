import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database.models import save_file, save_batch
from utils.filters import admin_filter
from utils.helpers import get_file_info
from config import Config

logger = logging.getLogger(__name__)

FILE_FILTER = (
    filters.document | filters.video | filters.audio |
    filters.photo | filters.voice | filters.video_note |
    filters.sticker | filters.animation
)

# In-memory batch sessions: {user_id: {"files": [...], "name": str}}
_batch_sessions: dict = {}


def inject_sessions(client: Client):
    client._batch_sessions = _batch_sessions


@Client.on_message(admin_filter & filters.command("batch") & filters.private)
async def batch_start(client: Client, message: Message):
    user_id = message.from_user.id
    if not hasattr(client, "_batch_sessions"):
        client._batch_sessions = _batch_sessions
    _batch_sessions[user_id] = {"files": [], "name": "Batch"}
    await message.reply_text(
        "📦 <b>Batch mode started!</b>\n\n"
        "Send files one by one.\n"
        "When done, send /done to finish and get your batch link.\n"
        "Send /cancel to abort.",
        parse_mode="html"
    )


@Client.on_message(admin_filter & filters.command("custombatch") & filters.private)
async def custombatch_start(client: Client, message: Message):
    user_id = message.from_user.id
    args = message.command
    if not hasattr(client, "_batch_sessions"):
        client._batch_sessions = _batch_sessions

    if len(args) > 1:
        name = " ".join(args[1:])
        _batch_sessions[user_id] = {"files": [], "name": name}
        await message.reply_text(
            f"📦 <b>Custom Batch started!</b>\n"
            f"📌 Name: <b>{name}</b>\n\n"
            "Send files one by one. Send /done when finished.",
            parse_mode="html"
        )
    else:
        _batch_sessions[user_id] = {"files": [], "name": None, "waiting_name": True}
        await message.reply_text("📝 Please send a <b>name</b> for this batch:", parse_mode="html")


@Client.on_message(admin_filter & filters.private)
async def batch_name_listener(client: Client, message: Message):
    user_id = message.from_user.id
    if not hasattr(client, "_batch_sessions"):
        return
    session = _batch_sessions.get(user_id)
    if not session or not session.get("waiting_name"):
        return
    if message.text and not message.text.startswith("/"):
        session["name"] = message.text.strip()
        session.pop("waiting_name", None)
        await message.reply_text(
            f"✅ Batch name set to: <b>{session['name']}</b>\n\nNow send files. Send /done when finished.",
            parse_mode="html"
        )


@Client.on_message(admin_filter & FILE_FILTER & filters.private)
async def batch_file_collector(client: Client, message: Message):
    user_id = message.from_user.id
    if not hasattr(client, "_batch_sessions"):
        return
    session = _batch_sessions.get(user_id)
    if not session or session.get("waiting_name"):
        return

    file_id, file_type, file_name, file_size = await get_file_info(message)
    if not file_id:
        return

    try:
        forwarded = await message.forward(Config.LOG_CHANNEL)
        uid = await save_file(
            file_id=file_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            caption=message.caption or "",
            message_id=forwarded.id,
            uploaded_by=user_id
        )
        session["files"].append(uid)
        count = len(session["files"])
        await message.reply_text(f"✅ File {count} added — <b>{file_name}</b> (Total: {count} files)", parse_mode="html")
    except Exception as e:
        logger.error(f"batch_file_collector error: {e}")
        await message.reply_text(f"❌ Error adding file: {e}")


@Client.on_message(admin_filter & filters.command("done") & filters.private)
async def batch_done(client: Client, message: Message):
    user_id = message.from_user.id
    if not hasattr(client, "_batch_sessions"):
        return await message.reply_text("❌ No active batch session.")
    session = _batch_sessions.pop(user_id, None)
    if not session:
        return await message.reply_text("❌ No active batch session.")

    files = session.get("files", [])
    if not files:
        return await message.reply_text("❌ No files were added to the batch.")

    name = session.get("name") or "Batch"
    batch_id = await save_batch(name, files, user_id)
    bot_info = await client.get_me()
    link = f"https://t.me/{bot_info.username}?start=batch_{batch_id}"

    await message.reply_text(
        f"✅ <b>Batch Created!</b>\n\n"
        f"📌 <b>Name:</b> {name}\n"
        f"📦 <b>Files:</b> {len(files)}\n\n"
        f"🔗 <b>Batch Link:</b>\n<code>{link}</code>",
        parse_mode="html"
    )


@Client.on_message(admin_filter & filters.command("cancel") & filters.private)
async def batch_cancel(client: Client, message: Message):
    user_id = message.from_user.id
    if hasattr(client, "_batch_sessions") and user_id in client._batch_sessions:
        client._batch_sessions.pop(user_id)
        await message.reply_text("❌ Batch session cancelled.")
    else:
        await message.reply_text("No active batch session.")
