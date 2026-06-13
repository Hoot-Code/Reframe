"""
handlers.py 
All user-facing conversation handlers:
  /start, /help, /stats, /cancel, /lang
  receive_media → size → mode → format → process
"""

import asyncio
import os
import time
import uuid
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import ContextTypes, ConversationHandler

from config import (
    CONFIG, ADMIN_IDS, TEMP_DIR, PRESET_SIZES,
    SELECT_LANG, SELECT_SIZE, CUSTOM_SIZE, SELECT_MODE, SELECT_FORMAT,
)
from database import db
from locales import t, LANGUAGE_NAMES
from scanner import scan_file
from media_processor import (
    process_image_sync, process_video_sync,
    IMAGE_FORMATS, VIDEO_FORMATS,
)
from utils import safe_delete

logger = logging.getLogger(__name__)

# One semaphore shared across all users
_job_sem = asyncio.Semaphore(CONFIG["max_concurrent_jobs"])

# Set of user IDs currently processing (survives context.user_data clears)
_processing_users: set[int] = set()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _lang(user_id: int) -> str:
    return db.get_user_language(user_id)


def _kb(*rows):
    """Build InlineKeyboardMarkup from rows of (text, data) tuples."""
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(txt, callback_data=dat) for txt, dat in row]
         for row in rows]
    )


# ─────────────────────────────────────────────────────────────────────────────
# /start
# ─────────────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.upsert_user(user)
    context.user_data.clear()

    # Always show language picker so user can confirm / change
    buttons = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
               for code, name in LANGUAGE_NAMES.items()]
    await update.message.reply_text(
        t("en", "choose_language"),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECT_LANG


async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_", 1)[1]   # e.g. "lang_ru" → "ru"
    user = update.effective_user

    db.set_user_language(user.id, lang)

    await query.edit_message_text(
        t(lang, "language_set"), parse_mode=ParseMode.MARKDOWN
    )
    await query.message.reply_text(
        t(lang, "welcome", name=user.first_name),
        parse_mode=ParseMode.MARKDOWN,
    )
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# /lang  (change language at any time)
# ─────────────────────────────────────────────────────────────────────────────
async def lang_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [[InlineKeyboardButton(name, callback_data=f"lang_{code}")]
               for code, name in LANGUAGE_NAMES.items()]
    await update.message.reply_text(
        t("en", "choose_language"),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECT_LANG


# ─────────────────────────────────────────────────────────────────────────────
# /help
# ─────────────────────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = _lang(update.effective_user.id)
    await update.message.reply_text(
        t(lang, "help_text"), parse_mode=ParseMode.MARKDOWN
    )


# ─────────────────────────────────────────────────────────────────────────────
# /stats
# ─────────────────────────────────────────────────────────────────────────────
async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    lang = _lang(user.id)
    row  = db.get_user(user.id)

    if not row:
        await update.message.reply_text(t(lang, "no_stats"))
        return

    total    = (row["photos_processed"] or 0) + (row["videos_processed"] or 0)
    joined   = (row["joined_date"] or "?")[:10]
    proc_t   = int(row["total_processing_time"] or 0)
    last_sz  = row["last_size"] or "—"
    status   = "🛑 BANNED" if row["is_banned"] else "✅ Active"

    await update.message.reply_text(
        t(lang, "stats_text",
          name=user.first_name, joined=joined,
          photos=row["photos_processed"] or 0,
          videos=row["videos_processed"] or 0,
          total=total, time=proc_t,
          last_size=last_sz, status=status),
        parse_mode=ParseMode.MARKDOWN,
    )


# ─────────────────────────────────────────────────────────────────────────────
# /cancel
# ─────────────────────────────────────────────────────────────────────────────
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang") or _lang(update.effective_user.id)
    inp  = context.user_data.get("input")
    if inp:
        asyncio.create_task(safe_delete([inp]))
    context.user_data.clear()
    await update.message.reply_text(t(lang, "cancelled"), parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# receive_media  (entry point for the processing conversation)
# ─────────────────────────────────────────────────────────────────────────────
async def receive_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg  = update.message
    row  = db.get_user(user.id)
    lang = _lang(user.id)

    # ── Guards ────────────────────────────────────────────────────────────────
    if row and row["is_banned"]:
        await msg.reply_text(t(lang, "banned"), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if CONFIG["maintenance_mode"] and user.id not in ADMIN_IDS:
        await msg.reply_text(t(lang, "maintenance"), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if user.id in _processing_users:
        await msg.reply_text(t(lang, "processing_wait"))
        return ConversationHandler.END

    # ── Identify media ────────────────────────────────────────────────────────
    file_id = None
    m_type  = None
    ext     = ".bin"

    if msg.photo:
        file_id = msg.photo[-1].file_id
        m_type  = "photo"
        ext     = ".jpg"

    elif msg.video:
        file_id = msg.video.file_id
        m_type  = "video"
        ext     = ".mp4"

    elif msg.document:
        mime = msg.document.mime_type or ""
        fname = msg.document.file_name or ""
        raw_ext = os.path.splitext(fname)[1].lower()

        if mime.startswith("image/"):
            file_id = msg.document.file_id
            m_type  = "photo"
            ext     = raw_ext if raw_ext in (".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp") else ".jpg"
        elif mime.startswith("video/"):
            file_id = msg.document.file_id
            m_type  = "video"
            ext     = raw_ext if raw_ext in (".mp4", ".mov", ".avi", ".mkv", ".webm") else ".mp4"
        else:
            await msg.reply_text(t(lang, "unsupported_type"), parse_mode=ParseMode.MARKDOWN)
            return ConversationHandler.END
    else:
        return ConversationHandler.END

    # ── Download ──────────────────────────────────────────────────────────────
    status_msg = await msg.reply_text(t(lang, "downloading"), parse_mode=ParseMode.MARKDOWN)
    try:
        tg_file = await context.bot.get_file(file_id)
        max_bytes = CONFIG["max_file_size_mb"] * 1024 * 1024

        if tg_file.file_size and tg_file.file_size > max_bytes:
            await status_msg.edit_text(
                t(lang, "file_too_large",
                  max_mb=CONFIG["max_file_size_mb"],
                  file_mb=tg_file.file_size / 1024 / 1024),
                parse_mode=ParseMode.MARKDOWN,
            )
            return ConversationHandler.END

        fname = f"{user.id}_{uuid.uuid4().hex}{ext}"
        fpath = os.path.join(TEMP_DIR, fname)
        await tg_file.download_to_drive(fpath)

        if not os.path.exists(fpath) or os.path.getsize(fpath) == 0:
            raise OSError("Downloaded file is empty or missing")

    except Exception as exc:
        logger.error(f"Download failed for user {user.id}: {exc}")
        await status_msg.edit_text(
            t(lang, "download_failed", error=str(exc)[:120]),
            parse_mode=ParseMode.MARKDOWN,
        )
        return ConversationHandler.END

    # ── Security scan ──────────────────────────────────────────────────────────
    await status_msg.edit_text(t(lang, "scanning"), parse_mode=ParseMode.MARKDOWN)
    safe, reason = scan_file(fpath, m_type)
    if not safe:
        db.log_security_event(user.id, fpath, reason)
        asyncio.create_task(safe_delete([fpath]))
        await status_msg.edit_text(
            t(lang, "scan_failed", reason=reason),
            parse_mode=ParseMode.MARKDOWN,
        )
        logger.warning(f"[SECURITY] User {user.id} sent dangerous file: {reason}")
        return ConversationHandler.END

    # ── Store state ────────────────────────────────────────────────────────────
    context.user_data.update({"input": fpath, "type": m_type, "lang": lang})

    # ── Build size keyboard ────────────────────────────────────────────────────
    kb_rows = []

    if row and row["last_size"]:
        kb_rows.append([
            (t(lang, "last_size_btn", size=row["last_size"]), f"sz_{row['last_size']}")
        ])

    kb_rows.append([(t(lang, "compress_btn"), "sz_compress")])

    for label, (w, h) in PRESET_SIZES.items():
        kb_rows.append([(label, f"sz_{w}x{h}")])

    kb_rows.append([
        (t(lang, "custom_btn"), "sz_custom"),
        (t(lang, "cancel_btn"), "sz_cancel"),
    ])

    await status_msg.edit_text(
        t(lang, "select_size"),
        reply_markup=_kb(*kb_rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECT_SIZE


# ─────────────────────────────────────────────────────────────────────────────
# SELECT_SIZE  callback
# ─────────────────────────────────────────────────────────────────────────────
async def size_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = context.user_data.get("lang", "en")
    data = query.data

    if data == "sz_cancel":
        asyncio.create_task(safe_delete([context.user_data.get("input")]))
        context.user_data.clear()
        await query.edit_message_text(t(lang, "cancelled"), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END

    if data == "sz_compress":
        context.user_data.update({"target": (0, 0), "mode": "compress"})
        return await _ask_format(query, context)

    if data == "sz_custom":
        await query.edit_message_text(
            t(lang, "send_dimensions"), parse_mode=ParseMode.MARKDOWN
        )
        return CUSTOM_SIZE

    # Preset / last-used  e.g. "sz_1920x1080"
    try:
        _, size_part = data.split("_", 1)
        w, h = map(int, size_part.split("x"))
        max_r = CONFIG["max_resolution"]
        if w > max_r or h > max_r:
            await query.edit_message_text(
                t(lang, "size_too_large", max_res=max_r, your_res=max(w, h)),
                parse_mode=ParseMode.MARKDOWN,
            )
            return SELECT_SIZE
        context.user_data["target"] = (w, h)
        return await _ask_mode(query, lang)
    except (ValueError, IndexError):
        await query.edit_message_text("❌ Invalid selection.")
        return ConversationHandler.END


# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM_SIZE  text handler
# ─────────────────────────────────────────────────────────────────────────────
async def custom_size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lang = context.user_data.get("lang", "en")
    raw  = (update.message.text or "").lower().replace("*", "x").replace("×", "x").replace(" ", "")

    parts = raw.split("x")
    if len(parts) != 2:
        await update.message.reply_text(t(lang, "invalid_format"), parse_mode=ParseMode.MARKDOWN)
        return CUSTOM_SIZE

    try:
        w, h = int(parts[0]), int(parts[1])
    except ValueError:
        await update.message.reply_text(t(lang, "invalid_format"), parse_mode=ParseMode.MARKDOWN)
        return CUSTOM_SIZE

    if w < 1 or h < 1:
        await update.message.reply_text(t(lang, "invalid_dims"), parse_mode=ParseMode.MARKDOWN)
        return CUSTOM_SIZE

    max_r = CONFIG["max_resolution"]
    if w > max_r or h > max_r:
        await update.message.reply_text(
            t(lang, "size_too_large", max_res=max_r, your_res=max(w, h)),
            parse_mode=ParseMode.MARKDOWN,
        )
        return CUSTOM_SIZE

    context.user_data["target"] = (w, h)
    return await _ask_mode(update.message, lang, is_message=True)


# ─────────────────────────────────────────────────────────────────────────────
# SELECT_MODE  callback
# ─────────────────────────────────────────────────────────────────────────────
async def mode_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["mode"] = query.data.split("_", 1)[1]   # "pad" or "stretch"
    return await _ask_format(query, context)


# ─────────────────────────────────────────────────────────────────────────────
# SELECT_FORMAT  callback  →  start processing
# ─────────────────────────────────────────────────────────────────────────────
async def format_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["output_format"] = query.data.split("_", 1)[1]   # e.g. "jpg"
    return await _process_media(update, context)


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────
async def _ask_mode(obj, lang: str, *, is_message: bool = False):
    markup = _kb(
        [(t(lang, "fit_btn"),    "mode_pad")],
        [(t(lang, "stretch_btn"), "mode_stretch")],
    )
    text = t(lang, "select_mode")
    if is_message:
        await obj.reply_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    else:
        await obj.edit_message_text(text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN)
    return SELECT_MODE


async def _ask_format(query, context: ContextTypes.DEFAULT_TYPE):
    lang   = context.user_data.get("lang", "en")
    m_type = context.user_data.get("type", "photo")

    keep = (t(lang, "keep_fmt_btn"), "fmt_keep")
    if m_type == "photo":
        rows = [
            [keep, ("JPG",  "fmt_jpg")],
            [("PNG", "fmt_png"), ("WEBP", "fmt_webp")],
        ]
    else:
        rows = [
            [keep, ("MP4", "fmt_mp4")],
            [("AVI", "fmt_avi"), ("MKV", "fmt_mkv")],
        ]

    await query.edit_message_text(
        t(lang, "select_format"),
        reply_markup=_kb(*rows),
        parse_mode=ParseMode.MARKDOWN,
    )
    return SELECT_FORMAT


async def _process_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Core processing step — called after all parameters are collected."""
    query   = update.callback_query
    user    = update.effective_user
    lang    = context.user_data.get("lang", "en")
    inp     = context.user_data.get("input")
    m_type  = context.user_data.get("type", "photo")
    mode    = context.user_data.get("mode", "pad")
    w, h    = context.user_data.get("target", (0, 0))
    raw_fmt = context.user_data.get("output_format", "keep")

    # Resolve "keep" to a sensible default based on type
    if raw_fmt == "keep":
        out_fmt = "jpg" if m_type == "photo" else "mp4"
    else:
        out_fmt = raw_fmt

    # Output extension
    if m_type == "photo":
        out_ext = IMAGE_FORMATS.get(out_fmt, ("JPEG", ".jpg"))[1]
    else:
        out_ext = VIDEO_FORMATS.get(out_fmt, ("libx264", ".mp4", "MP4"))[1]

    base   = os.path.splitext(inp)[0]
    outp   = f"{base}_out{out_ext}"
    size_s = f"{w}x{h}" if mode != "compress" else "compressed"
    is_cmp = (mode == "compress")

    db.update_last_size(user.id, size_s)
    _processing_users.add(user.id)
    t0 = time.time()

    try:
        if m_type == "photo":
            await query.edit_message_text(t(lang, "processing"), parse_mode=ParseMode.MARKDOWN)
            async with _job_sem:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        process_image_sync, inp, outp, w, h, mode, out_fmt, is_cmp
                    ),
                    timeout=CONFIG["process_timeout"],
                )
        else:
            await query.edit_message_text(t(lang, "rendering_video"), parse_mode=ParseMode.MARKDOWN)
            async with _job_sem:
                await asyncio.wait_for(
                    asyncio.to_thread(
                        process_video_sync, inp, outp, w, h, mode, out_fmt, is_cmp
                    ),
                    timeout=CONFIG["process_timeout"],
                )

        elapsed = time.time() - t0

        if not os.path.exists(outp) or os.path.getsize(outp) == 0:
            raise RuntimeError("Output file is missing or empty after processing")

        out_size = os.path.getsize(outp)
        fmt_lbl  = out_fmt.upper()

        await query.edit_message_text(t(lang, "uploading"), parse_mode=ParseMode.MARKDOWN)

        chat_id = update.effective_chat.id
        with open(outp, "rb") as fh:
            if m_type == "photo":
                cap = t(lang, "success_photo",
                        size=size_s, mode=mode, fmt=fmt_lbl, time=elapsed)
                await context.bot.send_photo(chat_id, fh, caption=cap,
                                             parse_mode=ParseMode.MARKDOWN)
            else:
                cap = t(lang, "success_video",
                        size=size_s, mode=mode, fmt=fmt_lbl,
                        time=elapsed, file_mb=out_size / 1024 / 1024)
                await context.bot.send_video(chat_id, fh, caption=cap,
                                             parse_mode=ParseMode.MARKDOWN,
                                             supports_streaming=True)

        await query.delete_message()

        db.increment_processed(user.id, m_type)
        db.add_processing_time(user.id, elapsed)
        db.log_process(user.id, m_type, size_s, mode, out_fmt, "success", elapsed)
        logger.info(f"[DONE] user={user.id} {m_type} {size_s} {out_fmt} {elapsed:.1f}s")

    except asyncio.TimeoutError:
        await query.edit_message_text(t(lang, "error_timeout"), parse_mode=ParseMode.MARKDOWN)
        db.log_process(user.id, m_type, size_s, mode, out_fmt,
                       "timeout", time.time() - t0, "timeout")

    except Exception as exc:
        err_str = str(exc)
        logger.error(f"[ERROR] user={user.id}: {err_str}")
        await query.edit_message_text(
            t(lang, "error_generic", error=err_str[:200]),
            parse_mode=ParseMode.MARKDOWN,
        )
        db.log_process(user.id, m_type, size_s, mode, out_fmt,
                       "error", time.time() - t0, err_str[:500])

    finally:
        _processing_users.discard(user.id)
        # Clean up both input and all possible output extensions
        to_del = [inp]
        if inp:
            b = os.path.splitext(inp)[0]
            for ex in (".jpg", ".png", ".webp", ".mp4", ".avi", ".mkv"):
                c = f"{b}_out{ex}"
                if c not in to_del:
                    to_del.append(c)
        asyncio.create_task(safe_delete(to_del))

    return ConversationHandler.END
