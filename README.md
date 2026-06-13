<div align="center">

>  فارسی: [README.fa.md](README.fa.md)


# 🦉 ReFrame


**A powerful Telegram bot for resizing, compressing, and converting photos & videos.**

*by [Hoot-Code](https://github.com/Hoot-Code)*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.5-blue)](https://python-telegram-bot.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-110%20passed-brightgreen)](#testing)

</div>

---

## ✨ Features

| Feature | Details |
|---|---|
| 📸 **Image processing** | Resize, compress, convert — JPG · PNG · WEBP |
| 🎬 **Video processing** | Resize, compress, convert — MP4 · AVI · MKV |
| 🗜️ **Compress mode** | Reduce file size without changing resolution |
| 🔄 **Format conversion** | Convert between supported image and video formats |
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
├── scanner.py           # Security scanner (lightweight pre-screening)
├── locales.py           # Strings in EN / RU / ZH / FA
├── utils.py             # Helpers (cleanup, safe_delete)
├── tests/               # Automated test suite
├── requirements.txt
├── Dockerfile
├── .env.example         # Template for secrets (copy to .env)
├── .gitignore
├── .dockerignore
└── temp_media/          # Created automatically at runtime
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
cp .env.example .env
```
Edit `.env` and fill in:
```
BOT_TOKEN=your_bot_token_here
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

> ⚠️ **Important:** This is a **lightweight pre-screening mechanism**, not a full security analysis. It provides a first line of defense against obvious threats but cannot guarantee file safety.

Every uploaded file is scanned **before** processing:

- **Magic-byte validation** — file header must match the claimed type (e.g. a `.jpg` must start with `FF D8 FF`)
- **Malicious-pattern detection** — rejects files containing PHP code, shell scripts, ELF/PE executables, or embedded ZIP archives
- **JPEG EOF validation** — verifies JPEG files end with the correct EOF marker
- **Events logged** — every blocked file is recorded in the `security_logs` table with user ID, threat description, and timestamp

### Limitations

The scanner **cannot** detect:
- Polymorphic or encrypted payloads
- Logic bombs or time-delayed exploits
- Steganographic content
- Decoder-specific vulnerabilities
- Memory-corruption triggers

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
| Twitter | 1200 × 675 |
| Facebook Cover | 820 × 312 |
| ✏️ Custom | any (up to 3840 px) |

---

## 📋 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather |
| `ADMIN_IDS` | ✅ | — | Comma-separated Telegram user IDs for admin access |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Maximum upload file size in MB |
| `MAX_CONCURRENT_JOBS` | ❌ | `2` | Maximum parallel processing jobs |

---

## 🧪 Testing

Run the test suite:
```bash
# Install test dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test module
pytest tests/test_scanner.py
```

### Test Coverage

| Module | Tests | Coverage |
|---|---|---|
| `scanner.py` | 25 tests | Magic bytes, malicious patterns, EOF validation, full scan |
| `database.py` | 20 tests | User CRUD, language prefs, settings, stats |
| `handlers.py` | 30 tests | Size parsing, format validation, mode validation, MD escaping |
| `config.py` | 11 tests | Env parsing, presets, conversation states |
| `locales.py` | 8 tests | Translation, formatting, key coverage |

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- FFmpeg
- SQLite (included with Python)

### Local Development
```bash
# Clone and setup
git clone https://github.com/Hoot-Code/ReFrame.git
cd ReFrame
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS

# Run
python main.py

# In another terminal — run tests
pytest -v
```

### Project Conventions
- **Code style:** PEP 8, no comments unless explaining non-obvious logic
- **Error handling:** Fail safely, log errors, never crash the bot
- **Security:** Validate all user inputs, scan all uploaded files
- **Testing:** Add tests for new features, maintain >90% coverage

---

## 🐛 Troubleshooting

### Bot doesn't start
- Check that `BOT_TOKEN` is set in `.env`
- Ensure FFmpeg is installed and accessible in PATH
- Verify Python 3.12+ is being used

### Files are rejected by scanner
- The scanner is a lightweight pre-screening tool
- Some legitimate files may be flagged if they contain unusual byte patterns
- Check `security_logs` in the admin panel for details

### Processing is slow
- Video processing depends on FFmpeg and file complexity
- Large files or high resolutions take longer
- Adjust `MAX_CONCURRENT_JOBS` to limit parallel processing

### Database errors
- The bot uses SQLite (file: `bot_data.db`)
- Ensure the bot has write permissions in the working directory
- Check disk space if writes fail

---

## 📄 License

MIT © [Hoot-Code](https://github.com/Hoot-Code)
