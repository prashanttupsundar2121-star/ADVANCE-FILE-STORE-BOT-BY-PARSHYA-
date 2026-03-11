import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database.models import (
    get_total_users, get_total_files, get_total_batches,
    get_all_admins, get_files_today, get_settings
)
from utils.filters import admin_filter
from utils.helpers import get_uptime

logger = logging.getLogger(__name__)


@Client.on_message(admin_filter & filters.command("stats") & filters.private)
async def stats_handler(client: Client, message: Message):
    await _send_stats(client, message)


@Client.on_callback_query(filters.regex("^show_stats$"))
async def stats_callback(client, callback_query):
    await _send_stats(client, callback_query.message, edit=True)
    await callback_query.answer()


async def _send_stats(client, message, edit=False):
    total_users = await get_total_users()
    total_files = await get_total_files()
    total_batches = await get_total_batches()
    admins = await get_all_admins()
    files_today = await get_files_today()
    settings = await get_settings()

    force_sub_channels = settings.get("force_sub_channels", [])
    active_fs = len([c for c in force_sub_channels if c])
    auto_del = settings.get("auto_delete_enabled", False)
    auto_del_sec = settings.get("auto_delete_seconds", 600)
    protect = settings.get("protect_content", False)
    maintenance = settings.get("bot_maintenance", False)
    uptime = get_uptime()

    text = (
        f"📊 <b>Bot Statistics</b>\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"👥 Total Users: <b>{total_users:,}</b>\n"
        f"📁 Total Files Stored: <b>{total_files:,}</b>\n"
        f"📦 Total Batches: <b>{total_batches:,}</b>\n"
        f"👮 Total Admins: <b>{len(admins)}</b>\n"
        f"📥 Files Delivered Today: <b>{files_today:,}</b>\n"
        f"📢 Active Force Sub Channels: <b>{active_fs}</b>\n"
        f"⏳ Auto Delete: <b>{'Enabled (' + str(auto_del_sec) + 's)' if auto_del else 'Disabled'}</b>\n"
        f"🔒 Protect Content: <b>{'Enabled' if protect else 'Disabled'}</b>\n"
        f"🔧 Maintenance Mode: <b>{'ON 🔴' if maintenance else 'OFF 🟢'}</b>\n"
        f"🕐 Bot Uptime: <b>{uptime}</b>"
    )

    if edit:
        await message.edit_text(text, parse_mode="html")
    else:
        await message.reply_text(text, parse_mode="html")
