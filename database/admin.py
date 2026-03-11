import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database.models import (
    ban_user, unban_user, get_user,
    add_admin, remove_admin, get_all_admins
)
from utils.filters import admin_filter, owner_filter, update_admin_cache
from config import Config

logger = logging.getLogger(__name__)


async def _reload_admin_cache():
    admins = await get_all_admins()
    ids = [a["_id"] for a in admins] + [Config.OWNER_ID]
    update_admin_cache(ids)
    return ids


# ─── BAN / UNBAN ──────────────────────────────────────────────────────────────

@Client.on_message(admin_filter & filters.command("ban") & filters.private)
async def ban_handler(client: Client, message: Message):
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")

    if not target_id:
        return await message.reply_text("❗ Usage: /ban <user_id> or reply to a user's message.")

    if target_id == Config.OWNER_ID:
        return await message.reply_text("❌ Cannot ban the owner.")

    await ban_user(target_id)
    await message.reply_text(f"🚫 User <code>{target_id}</code> has been banned.", parse_mode="html")

    try:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"🚫 User <code>{target_id}</code> banned by <a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name}</a>",
            parse_mode="html"
        )
    except Exception:
        pass


@Client.on_message(admin_filter & filters.command("unban") & filters.private)
async def unban_handler(client: Client, message: Message):
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")

    if not target_id:
        return await message.reply_text("❗ Usage: /unban <user_id> or reply to a user's message.")

    await unban_user(target_id)
    await message.reply_text(f"✅ User <code>{target_id}</code> has been unbanned.", parse_mode="html")


# ─── ADMIN MANAGEMENT ─────────────────────────────────────────────────────────

@Client.on_message(owner_filter & filters.command("addadmin") & filters.private)
async def addadmin_handler(client: Client, message: Message):
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
        name = message.reply_to_message.from_user.first_name
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
            name = str(target_id)
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")

    if not target_id:
        return await message.reply_text("❗ Usage: /addadmin <user_id>")

    await add_admin(target_id, name, message.from_user.id)
    await _reload_admin_cache()
    await message.reply_text(f"✅ User <code>{target_id}</code> added as admin.", parse_mode="html")


@Client.on_message(owner_filter & filters.command("removeadmin") & filters.private)
async def removeadmin_handler(client: Client, message: Message):
    target_id = None
    if message.reply_to_message:
        target_id = message.reply_to_message.from_user.id
    elif len(message.command) > 1:
        try:
            target_id = int(message.command[1])
        except ValueError:
            return await message.reply_text("❌ Invalid user ID.")

    if not target_id:
        return await message.reply_text("❗ Usage: /removeadmin <user_id>")

    if target_id == Config.OWNER_ID:
        return await message.reply_text("❌ Cannot remove the owner.")

    await remove_admin(target_id)
    await _reload_admin_cache()
    await message.reply_text(f"✅ User <code>{target_id}</code> removed from admins.", parse_mode="html")


@Client.on_message(admin_filter & filters.command("listadmins") & filters.private)
async def listadmins_handler(client: Client, message: Message):
    admins = await get_all_admins()
    if not admins:
        return await message.reply_text("No admins found.")

    text = "👮 <b>Current Admins:</b>\n\n"
    for a in admins:
        text += f"• <b>{a.get('name', 'N/A')}</b> — <code>{a['_id']}</code>\n"
    text += f"\n⭐ Owner: <code>{Config.OWNER_ID}</code>"
    await message.reply_text(text, parse_mode="html")


@Client.on_message(admin_filter & filters.command("reload") & filters.private)
async def reload_handler(client: Client, message: Message):
    ids = await _reload_admin_cache()
    from database.models import get_settings
    await get_settings()  # Refresh settings cache
    await message.reply_text(f"✅ Reloaded! {len(ids)} admins in cache.")


@Client.on_message(admin_filter & filters.command("maintenance") & filters.private)
async def maintenance_handler(client: Client, message: Message):
    from database.models import update_settings, get_settings
    args = message.command
    settings = await get_settings()
    current = settings.get("bot_maintenance", False)

    if len(args) > 1:
        if args[1].lower() == "on":
            await update_settings({"bot_maintenance": True})
            await message.reply_text("🔧 Maintenance mode <b>ENABLED</b>.", parse_mode="html")
        elif args[1].lower() == "off":
            await update_settings({"bot_maintenance": False})
            await message.reply_text("✅ Maintenance mode <b>DISABLED</b>.", parse_mode="html")
        else:
            await message.reply_text("❗ Usage: /maintenance on|off")
    else:
        new = not current
        await update_settings({"bot_maintenance": new})
        status = "ENABLED 🔴" if new else "DISABLED 🟢"
        await message.reply_text(f"🔧 Maintenance mode: <b>{status}</b>", parse_mode="html")


@Client.on_message(admin_filter & filters.command("logs") & filters.private)
async def logs_handler(client: Client, message: Message):
    try:
        await message.reply_document("bot.log", caption="📋 Recent bot logs")
    except Exception:
        await message.reply_text("❌ No log file found.")


@Client.on_message(admin_filter & filters.command("users") & filters.private)
async def users_handler(client: Client, message: Message):
    from database.models import get_recent_users
    users = await get_recent_users(20)
    if not users:
        return await message.reply_text("No users found.")

    text = "👥 <b>Recent 20 Users:</b>\n\n"
    for u in users:
        uname = f"@{u['username']}" if u.get("username") else "N/A"
        joined = u["joined"].strftime("%Y-%m-%d") if u.get("joined") else "N/A"
        text += f"• <b>{u.get('name', 'N/A')}</b> ({uname}) — <code>{u['_id']}</code> | {joined}\n"

    await message.reply_text(text, parse_mode="html")
