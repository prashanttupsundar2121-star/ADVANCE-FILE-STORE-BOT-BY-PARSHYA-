from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from utils.filters import admin_filter

HELP_TEXT = """
📚 <b>Help Menu</b>

<b>👤 User Commands:</b>
/start — Start the bot
/help — Show this menu

<b>👮 Admin Commands:</b>
/batch — Start batch file collection
/custombatch [name] — Batch with custom name
/getlink — Get shareable link (reply to file)
/deletelink — Delete a file link
/ban — Ban a user
/unban — Unban a user
/broadcast — Broadcast a message to all users
/stats — View bot statistics
/users — View recent users
/addadmin — Add new admin (Owner only)
/removeadmin — Remove an admin (Owner only)
/listadmins — View all admins
/settings — Open settings panel
/reload — Reload bot settings
/maintenance — Toggle maintenance mode
/logs — Get bot logs
"""


@Client.on_message(filters.command("help") & filters.private)
async def help_handler(client: Client, message: Message):
    await message.reply_text(
        HELP_TEXT,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="show_start")]
        ])
    )


@Client.on_callback_query(filters.regex("^show_help$"))
async def help_callback(client, callback_query):
    await callback_query.message.edit_text(
        HELP_TEXT,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="show_start")]
        ])
    )
    await callback_query.answer()


@Client.on_callback_query(filters.regex("^show_start$"))
async def back_to_start(client, callback_query):
    from database.models import get_settings
    from config import Config
    user = callback_query.from_user
    settings = await get_settings()
    welcome = settings.get("welcome_message", "👋 Welcome!")
    welcome = welcome.replace("{first_name}", user.first_name)
    welcome = welcome.replace("{username}", f"@{user.username}" if user.username else "N/A")
    welcome = welcome.replace("{user_id}", str(user.id))
    welcome = welcome.replace("{bot_name}", Config.BOT_NAME)
    await callback_query.message.edit_text(
        welcome,
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📚 Help", callback_data="show_help"),
             InlineKeyboardButton("📊 Stats", callback_data="show_stats")],
        ])
    )
    await callback_query.answer()
