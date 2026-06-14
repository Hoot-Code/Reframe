"""
config.py —
All settings, paths, conversation states, and logging live here.
Supports SQLite (default) and PostgreSQL backends.
"""

import os
import sys
import logging
from typing import Set

from dotenv import load_dotenv

load_dotenv()

# ── Logging (must be set up before any logger usage) ──────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)

# ── Token ──────────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")

# ── Admins ─────────────────────────────────────────────────────────────────────
ADMIN_IDS: Set[int] = set()
for _id in os.getenv("ADMIN_IDS", "").split(","):
    if _id.strip().isdigit():
        ADMIN_IDS.add(int(_id.strip()))

if not ADMIN_IDS:
    logger.warning("No ADMIN_IDS configured — admin panel will be inaccessible")

# ── Database backend ──────────────────────────────────────────────────────────
DB_BACKEND: str = os.getenv("DB_BACKEND", "sqlite")  # "sqlite" or "postgresql"
DB_FILE: str = os.getenv("DB_FILE", "bot_data.db")
DB_URL: str = os.getenv("DATABASE_URL", "")

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL: str = os.getenv("REDIS_URL", "")

# ── Paths ──────────────────────────────────────────────────────────────────────
TEMP_DIR = os.getenv("TEMP_DIR", "temp_media")
os.makedirs(TEMP_DIR, exist_ok=True)

# ── Feature flags ──────────────────────────────────────────────────────────────
FEATURE_FLAGS: dict = {
    "enable_rate_limiting":  os.getenv("FF_RATE_LIMITING", "true").lower() == "true",
    "enable_scanner":       os.getenv("FF_SCANNER", "true").lower() == "true",
    "enable_metrics":       os.getenv("FF_METRICS", "true").lower() == "true",
    "enable_tracing":       os.getenv("FF_TRACING", "false").lower() == "true",
}

# ── Runtime config ─────────────────────────────────────────────────────────────
def _int_env(key: str, default: int) -> int:
    try:
        return max(1, int(os.getenv(key, default)))
    except (ValueError, TypeError):
        return default

CONFIG: dict = {
    "maintenance_mode":       False,
    "max_concurrent_jobs":    _int_env("MAX_CONCURRENT_JOBS", 2),
    "max_file_size_mb":       _int_env("MAX_FILE_SIZE_MB",    50),
    "max_resolution":         3840,
    "process_timeout":        600,
    "video_crf":              23,
    "video_preset":           "medium",
    "max_video_bitrate":      "5M",
    "compress_image_quality": 55,
    "compress_video_crf":     32,
}

# ── Conversation states ────────────────────────────────────────────────────────
(
    SELECT_LANG,   # 0
    SELECT_SIZE,   # 1
    CUSTOM_SIZE,   # 2
    SELECT_MODE,   # 3
    SELECT_FORMAT, # 4
    ADMIN_MENU,    # 5
    ADMIN_INPUT,   # 6
) = range(7)

# ── Preset sizes ───────────────────────────────────────────────────────────────
PRESET_SIZES: dict = {
    "Insta Post  (1080x1080)": (1080, 1080),
    "Story       (1080x1920)": (1080, 1920),
    "HD          (1280x720)":  (1280,  720),
    "Full HD     (1920x1080)": (1920, 1080),
    "4K          (3840x2160)": (3840, 2160),
    "Twitter     (1200x675)":  (1200,  675),
    "Facebook    (820x312)":   (820,   312),
}
