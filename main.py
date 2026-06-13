"""
main.py — ReFrame Bot  |  creator: Hoot-Code
Entry point: registers all handlers, restores persisted settings, starts polling.

Python 3.14 fix: asyncio.get_event_loop() no longer auto-creates a loop in the
main thread.  We create and set one explicitly before calling run_polling().
"""

import asyncio
import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import (
    BOT_TOKEN, ADMIN_IDS, CONFIG,
    SELECT_LANG, SELECT_SIZE, CUSTOM_SIZE, SELECT_MODE, SELECT_FORMAT,
    ADMIN_MENU, ADMIN_INPUT,
)
from database import db
from utils import post_init

# ── Handler imports ────────────────────────────────────────────────────────────
from handlers import (
    start, language_callback, lang_command,
    help_command, stats_command, cancel_command,
    receive_media, size_callback, custom_size,
    mode_callback, format_callback,
)
from admin_handlers import (
    admin_entry, admin_callback, admin_input_handler,
)

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Build application
# ─────────────────────────────────────────────────────────────────────────────
def build_app():
    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ── /start  — language picker then welcome ─────────────────────────────────
    start_conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(language_callback, pattern=r"^lang_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
    )

    # ── /lang  — change language at any time ───────────────────────────────────
    lang_conv = ConversationHandler(
        entry_points=[CommandHandler("lang", lang_command)],
        states={
            SELECT_LANG: [
                CallbackQueryHandler(language_callback, pattern=r"^lang_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
    )

    # ── Media processing conversation ──────────────────────────────────────────
    media_conv = ConversationHandler(
        entry_points=[
            MessageHandler(
                (
                    filters.PHOTO
                    | filters.VIDEO
                    | filters.Document.IMAGE
                    | filters.Document.VIDEO
                ),
                receive_media,
            )
        ],
        states={
            SELECT_SIZE: [
                CallbackQueryHandler(size_callback, pattern=r"^sz_")
            ],
            CUSTOM_SIZE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, custom_size)
            ],
            SELECT_MODE: [
                CallbackQueryHandler(mode_callback, pattern=r"^mode_")
            ],
            SELECT_FORMAT: [
                CallbackQueryHandler(format_callback, pattern=r"^fmt_")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
        allow_reentry=True,
    )

    # ── Admin panel conversation ───────────────────────────────────────────────
    admin_conv = ConversationHandler(
        entry_points=[CommandHandler("admin", admin_entry)],
        states={
            ADMIN_MENU: [
                CallbackQueryHandler(admin_callback, pattern=r"^adm_"),
                CallbackQueryHandler(admin_callback, pattern=r"^ban_"),
            ],
            ADMIN_INPUT: [
                CallbackQueryHandler(admin_callback, pattern=r"^adm_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, admin_input_handler),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_command)],
    )

    # ── Register all handlers ──────────────────────────────────────────────────
    app.add_handler(start_conv)
    app.add_handler(lang_conv)
    app.add_handler(CommandHandler("help",  help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    app.add_handler(admin_conv)
    app.add_handler(media_conv)

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────
def main():
    # ── Restore persisted settings from DB ────────────────────────────────────
    restore_map = {
        "maintenance_mode":       lambda v: v == "True",
        "video_crf":              int,
        "video_preset":           str,
        "compress_image_quality": int,
        "max_file_size_mb":       int,
    }
    for key, cast in restore_map.items():
        val = db.get_setting(key)
        if val is not None:
            try:
                CONFIG[key] = cast(val)
            except (ValueError, TypeError):
                pass

    # ── Python 3.14 fix: explicitly create and set the event loop ─────────────
    # asyncio.get_event_loop() no longer auto-creates a loop in Python 3.14+
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    app = build_app()

    logger.info("=" * 55)
    logger.info("🦉  ReFrame Bot  |  by Hoot-Code")
    logger.info(f"    Admins configured : {len(ADMIN_IDS)}")
    logger.info(f"    Maintenance mode  : {CONFIG['maintenance_mode']}")
    logger.info(f"    Max concurrent    : {CONFIG['max_concurrent_jobs']}")
    logger.info(f"    Max file size     : {CONFIG['max_file_size_mb']} MB")
    logger.info(f"    Video CRF         : {CONFIG['video_crf']}  preset={CONFIG['video_preset']}")
    logger.info("=" * 55)
    print("\n✅  ReFrame Bot is running…  (Ctrl+C to stop)\n")

    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
