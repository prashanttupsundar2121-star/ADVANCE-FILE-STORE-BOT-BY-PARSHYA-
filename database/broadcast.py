import asyncio
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait, UserIsBlocked, InputUserDeactivated
from database.models import get_all_users, remove_admin
from utils.filters import admin_filter
from utils.keyboard import broadcast_type_keyboard

logger = logging.getLogger(__name__)

# State: {user_id: {"message": Message}}
_broadcast_state: dict = {}


@Client.on_message(admin_filter & filters.command("broadcast") & filters.private)
async def broadcast_handler(client: Client, message: Message):
    if not message.reply_to_message:
        return await message.reply_text(
            "❗ Reply to a message and send /broadcast to broadcast it to all users."
        )

    _broadcast_state[message.from_user.id] = {"message": message.reply_to_message}
    await message.reply_text(
        "📢 <b>Choose broadcast type:</b>",
        parse_mode="html",
        reply_markup=broadcast_type_keyboard()
    )


@Client.on_callback_query(filters.regex("^bc_(forward|copy|cancel)$"))
async def broadcast_type_callback(client, callback_query):
    user_id = callback_query.from_user.id
    state = _broadcast_state.pop(user_id, None)

    if not state:
        return await callback_query.answer("Session expired.", show_alert=True)

    action = callback_query.data.split("_")[1]
    if action == "cancel":
        await callback_query.message.edit_text("❌ Broadcast cancelled.")
        return

    msg_to_send = state["message"]
    await callback_query.message.edit_text("📢 Starting broadcast...")

    users = await get_all_users()
    total = len(users)
    sent = 0
    failed = 0

    status_msg = await callback_query.message.reply_text(f"📡 Broadcasting to {total} users...")

    for i, uid in enumerate(users):
        try:
            if action == "forward":
                await msg_to_send.forward(uid)
            else:
                await msg_to_send.copy(uid)
            sent += 1
        except (UserIsBlocked, InputUserDeactivated):
            failed += 1
        except FloodWait as e:
            await asyncio.sleep(e.value)
            try:
                if action == "forward":
                    await msg_to_send.forward(uid)
                else:
                    await msg_to_send.copy(uid)
                sent += 1
            except Exception:
                failed += 1
        except Exception:
            failed += 1

        if (i + 1) % 50 == 0:
            try:
                await status_msg.edit_text(
                    f"📡 Broadcasting...\n✔️ {sent}/{total} done | ❌ {failed} failed"
                )
            except Exception:
                pass

        await asyncio.sleep(0.05)

    await status_msg.edit_text(
        f"✅ <b>Broadcast Complete!</b>\n\n"
        f"📤 Sent: <b>{sent}</b>\n"
        f"❌ Failed: <b>{failed}</b>\n"
        f"👥 Total: <b>{total}</b>",
        parse_mode="html"
    )
