# 🚀 Advanced File Store Bot

A fully featured Telegram File Store Bot with MongoDB, batch system, force subscribe, inline settings panel, admin management, broadcast, and more.

---

## ✨ Features

| Feature | Details |
|---|---|
| 📁 File Store | Auto-generates shareable deep links |
| 📦 Batch | /batch + /custombatch with custom names |
| 📢 Force Sub | Up to 3 channels, manage via /settings |
| ⚙️ Settings Panel | Full inline menu — no config file editing needed |
| 👮 Admin System | Add/remove admins from within the bot |
| ⏳ Auto Delete | Configurable timer per file delivery |
| 🔒 Protect Content | Prevent file forwarding |
| 📨 Broadcast | Forward or copy mode with live progress |
| 🚫 Ban System | Ban/unban users instantly |
| 📊 Stats | Full usage statistics |

---

## ⚙️ Environment Variables

Copy `.env.example` to `.env` and fill in:

```env
API_ID=your_api_id
API_HASH=your_api_hash
BOT_TOKEN=your_bot_token
OWNER_ID=your_telegram_user_id
MONGO_URI=mongodb+srv://...
LOG_CHANNEL=-100xxxxxxxxxx
BOT_NAME=My File Store Bot
ADMINS=123456789,987654321
FORCE_SUB_CHANNEL_1=0
FORCE_SUB_CHANNEL_2=0
FORCE_SUB_CHANNEL_3=0
```

---

## 🚀 Deploy on Railway

1. Push this repo to GitHub
2. Go to [railway.app](https://railway.app) → New Project → Deploy from GitHub
3. Select your repo
4. Go to **Variables** tab → Add Raw Editor → paste all `.env` values
5. Click **Deploy** ✅

---

## 🖥️ Run Locally

```bash
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your values
python bot.py
```

---

## 📋 Commands

**User Commands:**
- `/start` — Start the bot
- `/help` — Show help menu

**Admin Commands:**
- `/batch` — Start batch collection
- `/custombatch [name]` — Named batch
- `/getlink` — Generate link (reply to file)
- `/deletelink <id>` — Delete file link
- `/ban <user_id>` — Ban user
- `/unban <user_id>` — Unban user
- `/broadcast` — Broadcast (reply to msg)
- `/stats` — Bot statistics
- `/users` — Recent users list
- `/addadmin <id>` — Add admin (owner only)
- `/removeadmin <id>` — Remove admin (owner only)
- `/listadmins` — List all admins
- `/settings` — Open settings panel
- `/reload` — Reload settings & admin cache
- `/maintenance on|off` — Toggle maintenance
- `/logs` — Get log file

---

## 🔒 Important Notes

- Bot must be **admin** in LOG_CHANNEL with post permission
- Bot must be **admin** in all Force Sub channels
- Only admins can store files (send files to bot in private)
- Owner ID has permanent access and cannot be removed
