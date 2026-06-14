<div align="center">

>  فارسی: [README.fa.md](README.fa.md)


# 🦉 ReFrame


**Enterprise-grade Telegram bot for resizing, compressing, and converting photos & videos.**

*by [Hoot-Code](https://github.com/Hoot-Code)*

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?logo=python)](https://python.org)
[![python-telegram-bot](https://img.shields.io/badge/python--telegram--bot-21.5-blue)](https://python-telegram-bot.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-124%20passed-brightgreen)](#testing)
[![CI](https://github.com/Hoot-Code/Reframe/actions/workflows/ci.yml/badge.svg)](https://github.com/Hoot-Code/Reframe/actions)

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
| 🛡️ **Admin panel** | Broadcast · ban/unban · stats · live config · health · shutdown |
| 💾 **Per-user history** | Remembers last used size |
| ⚡ **Concurrent jobs** | Semaphore-limited parallel processing |
| 🐘 **PostgreSQL** | Production-ready database with connection pooling |
| 📊 **Prometheus metrics** | Real-time monitoring with Grafana dashboards |
| 🔭 **OpenTelemetry** | Distributed tracing via OTLP |
| 🚀 **Kubernetes** | Auto-scaling deployment (2–10 pods) |
| 🏷️ **Feature flags** | Toggle features at runtime without redeployment |
| 🛡️ **Rate limiting** | Per-user file upload limits (5/minute) |
| 🔄 **Graceful shutdown** | In-flight jobs complete before exit |

---

## 🗂️ Project Structure

```
ReFrame/
├── main.py              # Entry point, bot startup
├── config.py            # Environment variables, feature flags & settings
├── database.py          # Dual-backend DatabaseManager (SQLite / PostgreSQL)
├── handlers.py          # User-facing conversation handlers
├── admin_handlers.py    # Admin panel (invisible to regular users)
├── media_processor.py   # Image & video processing (Pillow + FFmpeg)
├── scanner.py           # Security scanner (lightweight pre-screening)
├── locales.py           # Strings in EN / RU / ZH / FA
├── utils.py             # Helpers (cleanup, safe_delete)
├── metrics.py           # Prometheus metrics (/metrics endpoint)
├── tracing.py           # OpenTelemetry distributed tracing
├── tests/               # 124 automated tests
├── k8s/                 # Kubernetes manifests
├── monitoring/          # Prometheus + Grafana configuration
├── docker-compose.yml   # Full production stack
├── locustfile.py        # Load testing configuration
├── SECURITY.md          # Security policy & SOC 2 documentation
├── requirements.txt
├── pyproject.toml       # Modern Python packaging
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
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Or install with all optional extras:
pip install -e ".[all]"
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

### Docker (standalone)
```bash
docker build -t reframe-bot .
docker run -d --env-file .env --name reframe reframe-bot
```

### Docker Compose (full stack)
```bash
docker compose up -d
```
This starts: bot + PostgreSQL + Redis + Prometheus + Grafana

### Kubernetes
```bash
kubectl apply -f k8s/
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
| `/health` | Bot health check *(admin only)* |
| `/shutdown` | Graceful shutdown *(admin only)* |

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

> ⚠️ **Important:** This is a **lightweight pre-screening mechanism**, not a full security analysis.

Every uploaded file is scanned **before** processing:

- **Magic-byte validation** — file header must match the claimed type
- **Malicious-pattern detection** — rejects PHP, shell scripts, ELF/PE executables, embedded ZIP
- **JPEG EOF validation** — verifies JPEG files end with the correct EOF marker
- **Events logged** — every blocked file is recorded in `security_logs`

### Limitations

The scanner **cannot** detect:
- Polymorphic or encrypted payloads
- Logic bombs or time-delayed exploits
- Steganographic content
- Decoder-specific vulnerabilities
- Memory-corruption triggers

See [SECURITY.md](SECURITY.md) for full details and SOC 2 compliance notes.

---

## ⚙️ Admin Panel

Access `/admin` (only visible to user IDs listed in `ADMIN_IDS`):

- 📢 **Broadcast** — send a message to all users
- 👤 **Manage User** — look up any user, ban or unban
- 🚧 **Toggle Maintenance** — pause bot for all non-admin users
- 📊 **Full Stats** — detailed usage and success-rate breakdown
- 🔒 **Security Logs** — last 15 blocked threat events
- ⚙️ **Settings** — live-update CRF, preset, quality, max file size
- ❤️ **Health** — bot status, active jobs, uptime
- 🛑 **Shutdown** — graceful shutdown (finishes in-flight jobs)

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
| `DB_BACKEND` | ❌ | `sqlite` | Database backend: `sqlite` or `postgresql` |
| `DATABASE_URL` | ❌ | — | PostgreSQL connection URL |
| `REDIS_URL` | ❌ | — | Redis URL for distributed rate limiting |
| `MAX_FILE_SIZE_MB` | ❌ | `50` | Maximum upload file size in MB |
| `MAX_CONCURRENT_JOBS` | ❌ | `2` | Maximum parallel processing jobs |
| `FF_RATE_LIMITING` | ❌ | `true` | Enable per-user rate limiting |
| `FF_SCANNER` | ❌ | `true` | Enable security scanner |
| `FF_METRICS` | ❌ | `true` | Enable Prometheus metrics |
| `FF_TRACING` | ❌ | `false` | Enable OpenTelemetry tracing |

---

## 📊 Monitoring

### Prometheus Metrics

Metrics are exposed at `http://localhost:9090/metrics`:

| Metric | Type | Description |
|---|---|---|
| `reframe_commands_total` | counter | Commands received |
| `reframe_files_processed` | counter | Files processed successfully |
| `reframe_files_failed` | counter | Files that failed |
| `reframe_scan_threats` | counter | Threats detected |
| `reframe_active_jobs` | gauge | Currently processing jobs |
| `reframe_processing_time_seconds` | summary | Processing latency |

### Grafana Dashboard

Access Grafana at `http://localhost:3000` (admin/admin):
- Pre-configured dashboards for ReFrame metrics
- Auto-provisioned Prometheus datasource

---

## 🧪 Testing

### Run Tests
```bash
# All tests
pytest

# Verbose
pytest -v

# Specific module
pytest tests/test_scanner.py

# Integration tests only
pytest tests/test_integration.py tests/test_e2e.py
```

### Test Coverage

| Module | Tests | Coverage |
|---|---|---|
| `scanner.py` | 25 | Magic bytes, malicious patterns, EOF validation |
| `database.py` | 20 | User CRUD, language prefs, settings, stats, log rotation |
| `handlers.py` | 30 | Size parsing, format/mode validation, MD escaping |
| `config.py` | 11 | Env parsing, presets, conversation states |
| `locales.py` | 8 | Translation, formatting, key coverage |
| `integration` | 10 | Cross-module flows, rate limiting, log rotation |
| `e2e` | 20 | Handler flows with mocked Telegram API |
| **Total** | **124** | |

### Load Testing
```bash
# Install Locust
pip install locust

# Run load tests
locust -f locustfile.py --host=http://localhost:9090
```

---

## 🛠️ Development Setup

### Prerequisites
- Python 3.12+
- FFmpeg
- SQLite (included) or PostgreSQL

### Local Development
```bash
git clone https://github.com/Hoot-Code/ReFrame.git
cd ReFrame
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

cp .env.example .env
# Edit .env with your BOT_TOKEN and ADMIN_IDS

python main.py

# In another terminal
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
- Adjust `MAX_CONCURRENT_JOBS` to increase parallelism

### Database errors
- SQLite: ensure write permissions in working directory
- PostgreSQL: check `DATABASE_URL` and that the server is running
- Check disk space if writes fail

### Rate limiting triggered
- Default limit: 5 files per minute per user
- Disable with `FF_RATE_LIMITING=false` in `.env`
- Or wait 60 seconds before sending another file

---

## 📄 License

MIT © [Hoot-Code](https://github.com/Hoot-Code)
