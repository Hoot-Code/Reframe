"""
config.py —
All settings, paths, conversation states, and logging live here.
"""

import os
import sys
import logging
from typing import Set

from dotenv import load_dotenv

load_dotenv()

# ── Token ──────────────────────────────────────────────────────────────────────
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    sys.exit("CRITICAL: BOT_TOKEN missing in .env")

# ── Admins ─────────────────────────────────────────────────────────────────────
ADMIN_IDS: Set[int] = set()
for _id in os.getenv("ADMIN_IDS", "").split(","):
    if _id.strip().isdigit():
        ADMIN_IDS.add(int(_id.strip()))

# ── Paths ──────────────────────────────────────────────────────────────────────
TEMP_DIR = "temp_media"
DB_FILE  = "bot_data.db"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── Runtime config ─────────────────────────────────────────────────────────────
CONFIG: dict = {
    "maintenance_mode":       False,
    "max_concurrent_jobs":    int(os.getenv("MAX_CONCURRENT_JOBS", 2)),
    "max_file_size_mb":       int(os.getenv("MAX_FILE_SIZE_MB",    50)),
    "max_resolution":         3840,
    "process_timeout":        600,        # seconds
    "video_crf":              23,
    "video_preset":           "medium",
    "max_video_bitrate":      "5M",
    "compress_image_quality": 55,         # JPEG/WEBP quality for compress mode
    "compress_video_crf":     32,         # higher = smaller file
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
    "YouTube     (1280x720)":  (1280,  720),
    "TikTok      (1080x1920)": (1080, 1920),
    "Twitter     (1200x675)":  (1200,  675),
    "Facebook    (820x312)":   (820,   312),
}

# ── Logging ────────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)
