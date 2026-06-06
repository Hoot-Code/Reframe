<div align="center">

> **  فارسی:** [README.fa.md](README.fa.md)


# 🦉 ReFrame


**A powerful Telegram bot for resizing, compressing, and converting photos & videos.**

*by [Hoot-Code](https://github.com/Hoot-Code)*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.5-blue)](https://python-telegram-bot.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

</div>

---

## ✨ Features

| Feature | Details |
|---|---|
| 📸 **Image processing** | Resize, compress, convert — JPG · PNG · WEBP |
| 🎬 **Video processing** | Resize, compress, convert — MP4 · AVI · MKV |
| 🗜️ **Compress mode** | Reduce file size without changing resolution |
| 🔄 **Format conversion** | Convert between image and video formats |
| 🎯 **Fit / Stretch** | Maintain aspect ratio or force exact dimensions |
| 🔒 **Security scanner** | Magic-byte validation + malicious-pattern detection |
| 🌐 **4 languages** | English · Русский · 中文 · فارسی |
| 🛡️ **Admin panel** | Broadcast · ban/unban · stats · live config changes |
| 💾 **Per-user history** | Remembers last used size |
| ⚡ **Concurrent jobs** | Semaphore-limited parallel processing |

---

## 🗂️ Project Structure

```
ReFrame/
├── main.py              # Entry point, bot startup
├── config.py            # Environment variables & settings
├── database.py          # DatabaseManager (SQLite)
├── handlers.py          # User-facing conversation handlers
├── admin_handlers.py    # Admin panel (invisible to regular users)
├── media_processor.py   # Image & video processing (Pillow + FFmpeg)
├── scanner.py           # Security scanner
├── locales.py           # Strings in EN / RU / ZH / FA
├── utils.py             # Helpers (cleanup, safe_delete)
├── requirements.txt
├── Dockerfile
├── .env                 # Secrets (NOT committed)
├── .gitignore
└── temp_media/          # Created automatically
```

---

## 🚀 Quick Start

### 1. Clone
```bash
git clone https://github.com/Hoot-Code/ReFrame.git
cd ReFrame
```

### 2. Install dependencies
```bash
# Python 3.12+ required (also works on 3.14)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Install FFmpeg
```bash
# macOS
brew install ffmpeg

# Ubuntu / Debian
sudo apt install ffmpeg

# Windows — download from https://ffmpeg.org/download.html
```

### 4. Configure
```bash
cp .env .env.local   # or just edit .env
```
Fill in:
```
BOT_TOKEN=YOUR_BOT_TOKEN_HERE
ADMIN_IDS=123456789
```

### 5. Run
```bash
python main.py
```

### Docker
```bash
docker build -t reframe-bot .
docker run -d --env-file .env --name reframe reframe-bot
```

---

## 🤖 Bot Commands

| Command | Description |
|---|---|
| `/start` | Start the bot & choose language |
| `/help` | Full usage guide |
| `/stats` | Your processing statistics |
| `/lang` | Change language |
| `/cancel` | Cancel current operation |
| `/admin` | Admin panel *(admin only — invisible otherwise)* |

---

## 🌐 Supported Languages

| Code | Language |
|---|---|
| `en` | 🇺🇸 English |
| `ru` | 🇷🇺 Русский |
| `zh` | 🇨🇳 中文 |
| `fa` | 🇮🇷 فارسی |

Language is selected at first `/start` and can be changed any time with `/lang`.

---

## 🔒 Security Scanner

Every uploaded file is scanned **before** processing:

- **Magic-byte validation** — file header must match the claimed type (e.g. a `.jpg` must start with `FF D8 FF`)
- **Malicious-pattern detection** — rejects files containing PHP code, shell scripts, ELF/PE executables, or embedded ZIP archives
- **Events logged** — every blocked file is recorded in the `security_logs` table with user ID, threat description, and timestamp

---

## ⚙️ Admin Panel

Access `/admin` (only visible to user IDs listed in `ADMIN_IDS`):

- 📢 **Broadcast** — send a message to all users
- 👤 **Manage User** — look up any user, ban or unban
- 🚧 **Toggle Maintenance** — pause bot for all non-admin users
- 📊 **Full Stats** — detailed usage and success-rate breakdown
- 🔒 **Security Logs** — last 15 blocked threat events
- ⚙️ **Settings** — live-update CRF, preset, quality, max file size

---

## 🖼️ Preset Sizes

| Name | Resolution |
|---|---|
| Instagram Post | 1080 × 1080 |
| Instagram Story | 1080 × 1920 |
| HD | 1280 × 720 |
| Full HD | 1920 × 1080 |
| 4K | 3840 × 2160 |
| YouTube | 1280 × 720 |
| Twitter | 1200 × 675 |
| Facebook Cover | 820 × 312 |
| ✏️ Custom | any (up to 3840 px) |

---

## 📋 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token |
| `ADMIN_IDS` | ✅ | — | Comma-separated admin user IDs |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Max upload size |
| `MAX_CONCURRENT_JOBS` | ❌ | `2` | Parallel processing limit |

---

## 📄 License

MIT © [Hoot-Code](https://github.com/Hoot-Code)
