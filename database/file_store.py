import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database.models import save_file
from utils.filters import admin_filter
from utils.helpers import get_file_info
from utils.keyboard import file_link_keyboard
from config import Config

logger = logging.getLogger(__name__)

FILE_FILTER = (
    filters.document | filters.video | filters.audio |
    filters.photo | filters.voice | filters.video_note |
    filters.sticker | filters.animation
)


@Client.on_message(admin_filter & filters.private & FILE_FILTER)
async def file_store_handler(client: Client, message: Message):
    # Skip if in batch mode (handled by batch.py)
    if hasattr(client, "_batch_sessions") and message.from_user.id in client._batch_sessions:
        return

    processing = await message.reply_text("⏳ Storing file...")

    try:
        file_id, file_type, file_name, file_size = await get_file_info(message)
        if not file_id:
            return await processing.edit_text("❌ Unsupported file type.")

        caption = message.caption or ""

        # Forward to LOG_CHANNEL
        forwarded = await message.forward(Config.LOG_CHANNEL)

        # Save to DB
        uid = await save_file(
            file_id=file_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            caption=caption,
            message_id=forwarded.id,
            uploaded_by=message.from_user.id
        )

        if not uid:
            return await processing.edit_text("❌ Failed to store file in database.")

        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start=file_{uid}"

        await processing.edit_text(
            f"✅ <b>File Stored Successfully!</b>\n\n"
            f"📄 <b>Name:</b> <code>{file_name}</code>\n"
            f"📦 <b>Type:</b> {file_type}\n"
            f"🆔 <b>File ID:</b> <code>{uid}</code>\n\n"
            f"🔗 <b>Shareable Link:</b>\n<code>{link}</code>",
            parse_mode="html",
            reply_markup=file_link_keyboard(link)
        )

        # Log to channel
        try:
            await client.send_message(
                Config.LOG_CHANNEL,
                f"📁 New file stored!\n"
                f"👤 By: <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>\n"
                f"🆔 ID: <code>{uid}</code>\n"
                f"📄 Name: <code>{file_name}</code>",
                parse_mode="html"
            )
        except Exception:
            pass

    except Exception as e:
        logger.error(f"file_store_handler error: {e}")
        await processing.edit_text(f"❌ Error: <code>{e}</code>", parse_mode="html")


@Client.on_message(admin_filter & filters.command("getlink") & filters.private)
async def getlink_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("❗ Reply to a file with /getlink to generate its link.")

    reply = message.reply_to_message
    file_id, file_type, file_name, file_size = await get_file_info(reply)
    if not file_id:
        return await message.reply_text("❌ That message doesn't contain a valid file.")

    processing = await message.reply_text("⏳ Generating link...")

    try:
        forwarded = await reply.forward(Config.LOG_CHANNEL)
        uid = await save_file(
            file_id=file_id,
            file_type=file_type,
            file_name=file_name,
            file_size=file_size,
            caption=reply.caption or "",
            message_id=forwarded.id,
            uploaded_by=message.from_user.id
        )

        bot_info = await client.get_me()
        link = f"https://t.me/{bot_info.username}?start=file_{uid}"

        await processing.edit_text(
            f"🔗 <b>File Link Generated!</b>\n\n<code>{link}</code>",
            parse_mode="html",
            reply_markup=file_link_keyboard(link)
        )
    except Exception as e:
        logger.error(f"getlink_handler error: {e}")
        await processing.edit_text(f"❌ Error: <code>{e}</code>", parse_mode="html")


@Client.on_message(admin_filter & filters.command("deletelink") & filters.private)
async def deletelink_handler(client: Client, message: Message):
    args = message.command
    if len(args) < 2:
        return await message.reply_text("❗ Usage: /deletelink <file_id or link>")

    raw = args[1]
    # Extract ID from link if given
    if "?start=file_" in raw:
        uid = raw.split("?start=file_")[-1]
    else:
        uid = raw

    from database.models import get_file, delete_file
    doc = await get_file(uid)
    if not doc:
        return await message.reply_text("❌ File not found with that ID.")

    await delete_file(uid)
    await message.reply_text(f"✅ File <code>{uid}</code> deleted from database.", parse_mode="html")
