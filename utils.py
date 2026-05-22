"""
utils.py — Hoot-code Bot
Small shared utilities: startup cleanup, safe async file deletion.
"""

import os
import shutil
import asyncio
import logging

from telegram.ext import Application

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    """
    Called by PTB inside the running event loop right after the Application
    is initialised, before polling starts.  Cleans leftover temp files.
    """
    from config import TEMP_DIR
    logger.info("post_init: cleaning temp directory…")
    if os.path.isdir(TEMP_DIR):
        for name in os.listdir(TEMP_DIR):
            path = os.path.join(TEMP_DIR, name)
            try:
                if os.path.isfile(path) or os.path.islink(path):
                    os.unlink(path)
                elif os.path.isdir(path):
                    shutil.rmtree(path)
            except OSError as exc:
                logger.warning(f"Could not remove {path}: {exc}")
    logger.info("post_init: temp directory clean.")


async def safe_delete(paths: list) -> None:
    """
    Delete a list of file paths safely and quietly.
    Short delay so any pending reads finish first.
    """
    await asyncio.sleep(1.0)
    for p in paths:
        if p and os.path.exists(p):
            try:
                os.remove(p)
                logger.debug(f"Deleted: {p}")
            except OSError as exc:
                logger.warning(f"Could not delete {p}: {exc}")
