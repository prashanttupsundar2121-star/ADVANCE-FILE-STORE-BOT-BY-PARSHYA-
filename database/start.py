import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.models import add_user, get_user, is_banned, get_file, get_batch, get_settings, increment_download
from utils.helpers import check_force_sub, send_file_to_user
from utils.keyboard import join_channels_keyboard
from config import Config

logger = logging.getLogger(__name__)

# Rate limiting
_start_tracker: dict = {}


async def rate_limited(user_id: int) -> bool:
    import time
    now = time.time()
    times = _start_tracker.get(user_id, [])
    times = [t for t in times if now - t < 60]
    if len(times) >= 5:
        return True
    times.append(now)
    _start_tracker[user_id] = times
    return False


@Client.on_message(filters.command("start") & filters.private)
async def start_handler(client: Client, message: Message):
    user = message.from_user
    await add_user(user.id, user.first_name, user.username)

    if await is_banned(user.id):
        return await message.reply_text("🚫 You are banned from using this bot.")

    settings = await get_settings()
    if settings.get("bot_maintenance", False) and user.id not in Config.ADMINS:
        return await message.reply_text("🔧 Bot is currently under maintenance. Please try again later.")

    args = message.command
    if len(args) > 1:
        if await rate_limited(user.id):
            return await message.reply_text("⚠️ You're sending commands too fast. Please wait a moment.")

        param = args[1]

        # ── FILE DELIVERY ──
        if param.startswith("file_"):
            file_uid = param[5:]
            file_doc = await get_file(file_uid)
            if not file_doc:
                return await message.reply_text("❌ Invalid or expired link.")

            not_joined = await check_force_sub(client, user.id)
            if not_joined:
                return await message.reply_text(
                    "⚠️ You must join our channels to use this bot!",
                    reply_markup=join_channels_keyboard(not_joined)
                )

            protect = settings.get("protect_content", False)
            success = await send_file_to_user(client, message.chat.id, file_doc["message_id"], protect)
            if success:
                await increment_download(file_uid)
                try:
                    await client.send_message(
                        Config.LOG_CHANNEL,
                        f"📥 File `{file_uid}` downloaded by user `{user.id}` (@{user.username or 'N/A'})"
                    )
                except Exception:
                    pass

                if settings.get("auto_delete_enabled", False):
                    delay = settings.get("auto_delete_seconds", 600)
                    warn = await message.reply_text(
                        f"⚠️ This file will be automatically deleted in <b>{delay} seconds</b>!",
                        parse_mode="html"
                    )
                    await asyncio.sleep(delay)
                    try:
                        await warn.delete()
                        # Delete the sent files (last N messages)
                        async for msg in client.get_chat_history(message.chat.id, limit=5):
                            if msg.id != message.id and not msg.text:
                                await msg.delete()
                    except Exception:
                        pass
            else:
                await message.reply_text("❌ Failed to retrieve the file. Please try again.")
            return

        # ── BATCH DELIVERY ──
        if param.startswith("batch_"):
            batch_id = param[6:]
            batch = await get_batch(batch_id)
            if not batch:
                return await message.reply_text("❌ Invalid or expired batch link.")

            not_joined = await check_force_sub(client, user.id)
            if not_joined:
                return await message.reply_text(
                    "⚠️ You must join our channels to use this bot!",
                    reply_markup=join_channels_keyboard(not_joined)
                )

            protect = settings.get("protect_content", False)
            sent = await message.reply_text(f"📦 Sending <b>{len(batch['files'])}</b> files...", parse_mode="html")

            delivered = 0
            for fuid in batch["files"]:
                file_doc = await get_file(fuid)
                if file_doc:
                    ok = await send_file_to_user(client, message.chat.id, file_doc["message_id"], protect)
                    if ok:
                        delivered += 1
                        await increment_download(fuid)
                await asyncio.sleep(0.5)

            await sent.edit_text(f"✅ All <b>{delivered}</b> files delivered!", parse_mode="html")

            if settings.get("auto_delete_enabled", False):
                delay = settings.get("auto_delete_seconds", 600)
                warn = await message.reply_text(
                    f"⚠️ These files will be deleted in <b>{delay} seconds</b>!",
                    parse_mode="html"
                )
                await asyncio.sleep(delay)
                try:
                    await warn.delete()
                    async for msg in client.get_chat_history(message.chat.id, limit=delivered + 5):
                        if not msg.text:
                            await msg.delete()
                except Exception:
                    pass
            return

    # ── WELCOME MESSAGE ──
    welcome = settings.get("welcome_message", "👋 Welcome!")
    welcome = welcome.replace("{first_name}", user.first_name)
    welcome = welcome.replace("{username}", f"@{user.username}" if user.username else "N/A")
    welcome = welcome.replace("{user_id}", str(user.id))
    welcome = welcome.replace("{bot_name}", Config.BOT_NAME)

    await message.reply_text(
        welcome,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Help", callback_data="show_help"),
             InlineKeyboardButton("📊 Stats", callback_data="show_stats")],
        ])
    )


@Client.on_callback_query(filters.regex("^check_joined$"))
async def check_joined_callback(client, callback_query):
    user_id = callback_query.from_user.id
    not_joined = await check_force_sub(client, user_id)
    if not_joined:
        await callback_query.answer("❌ You haven't joined all required channels yet!", show_alert=True)
    else:
        await callback_query.answer("✅ You have joined all channels!", show_alert=True)
        await callback_query.message.delete()
