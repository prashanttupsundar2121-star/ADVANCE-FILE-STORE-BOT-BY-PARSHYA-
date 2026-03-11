import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from database.models import (
    get_settings, update_settings, add_admin, remove_admin, get_all_admins
)
from utils.filters import admin_filter, update_admin_cache
from utils.keyboard import (
    main_settings_keyboard, forcesub_keyboard, autodelete_keyboard,
    protect_keyboard, maintenance_keyboard
)
from config import Config

logger = logging.getLogger(__name__)

# Conversation states: {user_id: {"action": str, ...}}
_settings_state: dict = {}


@Client.on_message(admin_filter & filters.command("settings") & filters.private)
async def settings_handler(client: Client, message: Message):
    await message.reply_text(
        "⚙️ <b>Bot Settings Panel</b>\n\nChoose a section to configure:",
        parse_mode="html",
        reply_markup=main_settings_keyboard()
    )


# ─── MAIN MENU ────────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_main$"))
async def settings_main(client, cq):
    await cq.message.edit_text(
        "⚙️ <b>Bot Settings Panel</b>\n\nChoose a section to configure:",
        parse_mode="html",
        reply_markup=main_settings_keyboard()
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^settings_close$"))
async def settings_close(client, cq):
    await cq.message.delete()
    await cq.answer("Closed.")


# ─── FORCE SUBSCRIBE ──────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_forcesub$"))
async def settings_forcesub(client, cq):
    settings = await get_settings()
    enabled = settings.get("force_sub_enabled", False)
    channels = settings.get("force_sub_channels", [])
    text = (
        f"📢 <b>Force Subscribe Settings</b>\n\n"
        f"Status: {'✅ ENABLED' if enabled else '❌ DISABLED'}\n"
        f"Channels: {len(channels)}/3 configured"
    )
    await cq.message.edit_text(text, parse_mode="html", reply_markup=forcesub_keyboard(settings))
    await cq.answer()


@Client.on_callback_query(filters.regex("^fs_toggle$"))
async def fs_toggle(client, cq):
    settings = await get_settings()
    new = not settings.get("force_sub_enabled", False)
    await update_settings({"force_sub_enabled": new})
    settings["force_sub_enabled"] = new
    await cq.message.edit_reply_markup(forcesub_keyboard(settings))
    await cq.answer(f"Force Sub {'Enabled ✅' if new else 'Disabled ❌'}")


@Client.on_callback_query(filters.regex(r"^fs_add_(\d)$"))
async def fs_add(client, cq):
    slot = int(cq.data.split("_")[-1])
    _settings_state[cq.from_user.id] = {"action": "fs_add", "slot": slot}
    await cq.message.reply_text(
        f"📢 Send the <b>Channel ID</b> or forward a message from the channel to add as Force Sub Channel {slot+1}:",
        parse_mode="html"
    )
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^fs_remove_(\d)$"))
async def fs_remove(client, cq):
    slot = int(cq.data.split("_")[-1])
    settings = await get_settings()
    channels = settings.get("force_sub_channels", [])
    if slot < len(channels):
        channels.pop(slot)
        await update_settings({"force_sub_channels": channels})
        settings["force_sub_channels"] = channels
    await cq.message.edit_reply_markup(forcesub_keyboard(settings))
    await cq.answer(f"Channel {slot+1} removed.")


# ─── AUTO DELETE ──────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_autodelete$"))
async def settings_autodelete(client, cq):
    settings = await get_settings()
    await cq.message.edit_text(
        "⏳ <b>Auto Delete Settings</b>",
        parse_mode="html",
        reply_markup=autodelete_keyboard(settings)
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^ad_toggle$"))
async def ad_toggle(client, cq):
    settings = await get_settings()
    new = not settings.get("auto_delete_enabled", False)
    await update_settings({"auto_delete_enabled": new})
    settings["auto_delete_enabled"] = new
    await cq.message.edit_reply_markup(autodelete_keyboard(settings))
    await cq.answer(f"Auto Delete {'Enabled ✅' if new else 'Disabled ❌'}")


@Client.on_callback_query(filters.regex("^ad_set_delay$"))
async def ad_set_delay(client, cq):
    _settings_state[cq.from_user.id] = {"action": "ad_set_delay"}
    await cq.message.reply_text("⏱️ Send the number of <b>seconds</b> for auto-delete delay (e.g., 300):", parse_mode="html")
    await cq.answer()


# ─── PROTECT CONTENT ──────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_protect$"))
async def settings_protect(client, cq):
    settings = await get_settings()
    await cq.message.edit_text(
        "🔒 <b>Protect Content Settings</b>\n\nWhen enabled, users cannot forward files.",
        parse_mode="html",
        reply_markup=protect_keyboard(settings)
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^pc_toggle$"))
async def pc_toggle(client, cq):
    settings = await get_settings()
    new = not settings.get("protect_content", False)
    await update_settings({"protect_content": new})
    settings["protect_content"] = new
    await cq.message.edit_reply_markup(protect_keyboard(settings))
    await cq.answer(f"Protect Content {'ON ✅' if new else 'OFF ❌'}")


# ─── MAINTENANCE ──────────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_maintenance$"))
async def settings_maintenance(client, cq):
    settings = await get_settings()
    await cq.message.edit_text(
        "🔧 <b>Maintenance Mode</b>",
        parse_mode="html",
        reply_markup=maintenance_keyboard(settings)
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^mt_toggle$"))
async def mt_toggle(client, cq):
    settings = await get_settings()
    new = not settings.get("bot_maintenance", False)
    await update_settings({"bot_maintenance": new})
    settings["bot_maintenance"] = new
    await cq.message.edit_reply_markup(maintenance_keyboard(settings))
    await cq.answer(f"Maintenance {'ON 🔴' if new else 'OFF 🟢'}")


# ─── ADMIN MANAGEMENT ─────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_admins$"))
async def settings_admins(client, cq):
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    admins = await get_all_admins()
    rows = []
    for a in admins:
        if a["_id"] != Config.OWNER_ID:
            rows.append([
                InlineKeyboardButton(f"👤 {a.get('name', 'N/A')} ({a['_id']})", callback_data="noop"),
                InlineKeyboardButton("➖ Remove", callback_data=f"sa_remove_{a['_id']}")
            ])
    rows.append([InlineKeyboardButton("➕ Add New Admin", callback_data="sa_add")])
    rows.append([InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")])

    text = f"👮 <b>Admin Management</b>\n\n⭐ Owner: <code>{Config.OWNER_ID}</code>\n\nAdmins: {len(admins)}"
    await cq.message.edit_text(text, parse_mode="html", reply_markup=InlineKeyboardMarkup(rows))
    await cq.answer()


@Client.on_callback_query(filters.regex(r"^sa_remove_(\d+)$"))
async def sa_remove(client, cq):
    uid = int(cq.data.split("_")[-1])
    if uid == Config.OWNER_ID:
        return await cq.answer("Cannot remove owner.", show_alert=True)
    await remove_admin(uid)
    admins_list = await get_all_admins()
    update_admin_cache([a["_id"] for a in admins_list] + [Config.OWNER_ID])
    await cq.answer(f"Admin {uid} removed.")
    # Refresh panel
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    admins = await get_all_admins()
    rows = []
    for a in admins:
        if a["_id"] != Config.OWNER_ID:
            rows.append([
                InlineKeyboardButton(f"👤 {a.get('name', 'N/A')} ({a['_id']})", callback_data="noop"),
                InlineKeyboardButton("➖ Remove", callback_data=f"sa_remove_{a['_id']}")
            ])
    rows.append([InlineKeyboardButton("➕ Add New Admin", callback_data="sa_add")])
    rows.append([InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")])
    text = f"👮 <b>Admin Management</b>\n\n⭐ Owner: <code>{Config.OWNER_ID}</code>\n\nAdmins: {len(admins)}"
    await cq.message.edit_text(text, parse_mode="html", reply_markup=InlineKeyboardMarkup(rows))


@Client.on_callback_query(filters.regex("^sa_add$"))
async def sa_add(client, cq):
    _settings_state[cq.from_user.id] = {"action": "sa_add"}
    await cq.message.reply_text("👤 Send the <b>User ID</b> of the new admin:", parse_mode="html")
    await cq.answer()


# ─── WELCOME MESSAGE ──────────────────────────────────────────────────────────

@Client.on_callback_query(filters.regex("^settings_welcome$"))
async def settings_welcome(client, cq):
    settings = await get_settings()
    current = settings.get("welcome_message", "Not set")
    from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    await cq.message.edit_text(
        f"📝 <b>Welcome Message</b>\n\n<b>Current:</b>\n<code>{current}</code>\n\n"
        "Available variables: <code>{first_name}</code>, <code>{username}</code>, <code>{user_id}</code>, <code>{bot_name}</code>",
        parse_mode="html",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("✏️ Edit Welcome Message", callback_data="sw_edit")],
            [InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")]
        ])
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^sw_edit$"))
async def sw_edit(client, cq):
    _settings_state[cq.from_user.id] = {"action": "sw_edit"}
    await cq.message.reply_text(
        "📝 Send your new <b>welcome message</b>.\nHTML formatting supported.\n"
        "Variables: <code>{first_name}</code>, <code>{username}</code>, <code>{user_id}</code>, <code>{bot_name}</code>",
        parse_mode="html"
    )
    await cq.answer()


@Client.on_callback_query(filters.regex("^settings_stats$"))
async def settings_stats_btn(client, cq):
    from plugins.stats import _send_stats
    await _send_stats(client, cq.message, edit=True)
    await cq.answer()


@Client.on_callback_query(filters.regex("^(noop|ad_status|pc_status|mt_status|fs_info_\d)$"))
async def noop_callback(client, cq):
    await cq.answer()


# ─── TEXT LISTENER FOR SETTINGS STATES ────────────────────────────────────────

@Client.on_message(admin_filter & filters.private & filters.text)
async def settings_text_listener(client: Client, message: Message):
    user_id = message.from_user.id
    state = _settings_state.get(user_id)
    if not state:
        return

    action = state.get("action")

    if action == "fs_add":
        slot = state.get("slot", 0)
        text = message.text.strip()
        try:
            ch_id = int(text) if text.lstrip("-").isdigit() else text
            settings = await get_settings()
            channels = settings.get("force_sub_channels", [])
            if slot < len(channels):
                channels[slot] = ch_id
            else:
                while len(channels) < slot:
                    channels.append(None)
                channels.append(ch_id)
            await update_settings({"force_sub_channels": channels})
            _settings_state.pop(user_id, None)
            await message.reply_text(f"✅ Channel {slot+1} set to: <code>{ch_id}</code>", parse_mode="html")
        except Exception as e:
            await message.reply_text(f"❌ Error: {e}")

    elif action == "ad_set_delay":
        try:
            seconds = int(message.text.strip())
            await update_settings({"auto_delete_seconds": seconds})
            _settings_state.pop(user_id, None)
            await message.reply_text(f"✅ Auto-delete delay set to <b>{seconds} seconds</b>.", parse_mode="html")
        except ValueError:
            await message.reply_text("❌ Please send a valid number.")

    elif action == "sa_add":
        try:
            new_id = int(message.text.strip())
            await add_admin(new_id, str(new_id), user_id)
            admins_list = await get_all_admins()
            update_admin_cache([a["_id"] for a in admins_list] + [Config.OWNER_ID])
            _settings_state.pop(user_id, None)
            await message.reply_text(f"✅ User <code>{new_id}</code> added as admin.", parse_mode="html")
        except ValueError:
            await message.reply_text("❌ Please send a valid user ID.")

    elif action == "sw_edit":
        new_msg = message.text
        await update_settings({"welcome_message": new_msg})
        _settings_state.pop(user_id, None)
        await message.reply_text("✅ Welcome message updated!")
