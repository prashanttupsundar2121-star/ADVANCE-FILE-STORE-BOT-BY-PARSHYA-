from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_settings_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📢 Force Subscribe", callback_data="settings_forcesub")],
        [InlineKeyboardButton("⏳ Auto Delete", callback_data="settings_autodelete")],
        [InlineKeyboardButton("🔒 Protect Content", callback_data="settings_protect")],
        [InlineKeyboardButton("👮 Admin Management", callback_data="settings_admins")],
        [InlineKeyboardButton("📝 Custom Welcome Message", callback_data="settings_welcome")],
        [InlineKeyboardButton("🔧 Maintenance Mode", callback_data="settings_maintenance")],
        [InlineKeyboardButton("📊 Bot Stats", callback_data="settings_stats")],
        [InlineKeyboardButton("❌ Close", callback_data="settings_close")],
    ])


def back_keyboard(callback="settings_main"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Main", callback_data=callback)]
    ])


def forcesub_keyboard(settings: dict):
    enabled = settings.get("force_sub_enabled", False)
    channels = settings.get("force_sub_channels", [])

    rows = []
    for i in range(3):
        if i < len(channels):
            rows.append([InlineKeyboardButton(
                f"📢 Channel {i+1}: {channels[i]}",
                callback_data=f"fs_info_{i}"
            ), InlineKeyboardButton("➖ Remove", callback_data=f"fs_remove_{i}")])
        else:
            rows.append([InlineKeyboardButton(
                f"📢 Channel {i+1}: Not Set",
                callback_data=f"fs_info_{i}"
            ), InlineKeyboardButton("➕ Add", callback_data=f"fs_add_{i}")])

    toggle_text = "❌ Disable Force Sub" if enabled else "✅ Enable Force Sub"
    rows.append([InlineKeyboardButton(toggle_text, callback_data="fs_toggle")])
    rows.append([InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")])
    return InlineKeyboardMarkup(rows)


def autodelete_keyboard(settings: dict):
    enabled = settings.get("auto_delete_enabled", False)
    seconds = settings.get("auto_delete_seconds", 600)
    toggle_text = "❌ Disable" if enabled else "✅ Enable"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Auto Delete: {'✅ ON' if enabled else '❌ OFF'}", callback_data="ad_status")],
        [InlineKeyboardButton(f"⏱️ Current Delay: {seconds}s", callback_data="ad_status")],
        [InlineKeyboardButton(toggle_text, callback_data="ad_toggle"),
         InlineKeyboardButton("⏱️ Set Delay", callback_data="ad_set_delay")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")],
    ])


def protect_keyboard(settings: dict):
    enabled = settings.get("protect_content", False)
    toggle_text = "Turn OFF 🔴" if enabled else "Turn ON 🟢"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Protect Content: {'ON ✅' if enabled else 'OFF ❌'}", callback_data="pc_status")],
        [InlineKeyboardButton(toggle_text, callback_data="pc_toggle")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")],
    ])


def maintenance_keyboard(settings: dict):
    enabled = settings.get("bot_maintenance", False)
    toggle_text = "Turn OFF 🟢" if enabled else "Turn ON 🔴"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Maintenance: {'ON 🔴' if enabled else 'OFF 🟢'}", callback_data="mt_status")],
        [InlineKeyboardButton(toggle_text, callback_data="mt_toggle")],
        [InlineKeyboardButton("🔙 Back to Main", callback_data="settings_main")],
    ])


def join_channels_keyboard(channels: list, bot_username: str = None):
    rows = []
    for i, ch in enumerate(channels):
        if isinstance(ch, str) and ch.startswith("@"):
            url = f"https://t.me/{ch.lstrip('@')}"
        else:
            url = f"https://t.me/c/{str(ch).lstrip('-100')}"
        rows.append([InlineKeyboardButton(f"📢 Join Channel {i+1}", url=url)])
    rows.append([InlineKeyboardButton("✅ I've Joined", callback_data="check_joined")])
    return InlineKeyboardMarkup(rows)


def broadcast_type_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📨 Forward", callback_data="bc_forward"),
         InlineKeyboardButton("📋 Copy", callback_data="bc_copy")],
        [InlineKeyboardButton("❌ Cancel", callback_data="bc_cancel")],
    ])


def file_link_keyboard(link: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Share Link", url=f"https://t.me/share/url?url={link}"),
         InlineKeyboardButton("📋 Copy Link", callback_data=f"copy_link|{link[:50]}")]
    ])
