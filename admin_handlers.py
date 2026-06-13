"""
admin_handlers.py — ReFrame Bot  |  creator: Hoot-Code
Admin-only panel: stats, broadcast, ban/unban, security logs, settings.
The /admin command is invisible in help and silently ignored for non-admins.
"""

import asyncio
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import Forbidden
from telegram.ext import ContextTypes, ConversationHandler

from config import CONFIG, ADMIN_IDS, ADMIN_MENU, ADMIN_INPUT
from database import db

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Guards
# ─────────────────────────────────────────────────────────────────────────────
def _is_admin(update: Update) -> bool:
    return update.effective_user.id in ADMIN_IDS


def _deny(query):
    return query.answer("⛔ Access denied.", show_alert=True)


# ─────────────────────────────────────────────────────────────────────────────
# Entry point  — /admin
# ─────────────────────────────────────────────────────────────────────────────
async def admin_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        # Silently ignore — do NOT reveal the panel exists
        return ConversationHandler.END
    await _render_panel(update)
    return ADMIN_MENU


# ─────────────────────────────────────────────────────────────────────────────
# Main panel renderer
# ─────────────────────────────────────────────────────────────────────────────
async def _render_panel(update: Update):
    stats = db.get_total_stats()
    sr = (stats["success_jobs"] / stats["total_jobs"] * 100
          if stats["total_jobs"] else 0.0)

    text = (
        "🛡️ *ReFrame — Admin Panel*\n"
        "📊 *Overview:*\n"
        f"👥 Users: `{stats['total_users']}`  |  🛑 Banned: `{stats['total_banned']}`\n"
        f"📸 Photos: `{stats['total_photos']}`  |  🎬 Videos: `{stats['total_videos']}`\n"
        f"⚙️ Jobs: `{stats['total_jobs']}`  |  ✅ Success: `{sr:.1f}%`\n"
        f"🚫 Threats blocked: `{stats['total_threats']}`\n\n"
        "⚙️ *Settings:*\n"
        f"🚧 Maintenance: {'🟢 ON' if CONFIG['maintenance_mode'] else '🔴 OFF'}\n"
        f"📁 Max file: `{CONFIG['max_file_size_mb']} MB`\n"
        f"🎬 CRF: `{CONFIG['video_crf']}` | Preset: `{CONFIG['video_preset']}`\n"
        f"🗜️ Compress quality: `{CONFIG['compress_image_quality']}`"
    )

    kb = [
        [InlineKeyboardButton("📢 Broadcast",        callback_data="adm_cast"),
         InlineKeyboardButton("👤 Manage User",       callback_data="adm_user")],
        [InlineKeyboardButton("🚧 Toggle Maintenance",callback_data="adm_maint"),
         InlineKeyboardButton("📊 Full Stats",        callback_data="adm_stats")],
        [InlineKeyboardButton("🔒 Security Logs",     callback_data="adm_seclogs"),
         InlineKeyboardButton("⚙️ Settings",          callback_data="adm_settings")],
        [InlineKeyboardButton("❌ Close",             callback_data="adm_close")],
    ]

    markup = InlineKeyboardMarkup(kb)
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(
                text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
            )
        except Exception:
            await update.callback_query.message.reply_text(
                text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
            )
    else:
        await update.message.reply_text(
            text, reply_markup=markup, parse_mode=ParseMode.MARKDOWN
        )


# ─────────────────────────────────────────────────────────────────────────────
# Admin panel callbacks  (ADMIN_MENU state)
# ─────────────────────────────────────────────────────────────────────────────
async def admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not _is_admin(update):
        await _deny(query)
        return ConversationHandler.END
    await query.answer()

    data = query.data

    # ── Close ──────────────────────────────────────────────────────────────────
    if data == "adm_close":
        await query.delete_message()
        return ConversationHandler.END

    # ── Back ───────────────────────────────────────────────────────────────────
    if data == "adm_back":
        await _render_panel(update)
        return ADMIN_MENU

    # ── Toggle maintenance ─────────────────────────────────────────────────────
    if data == "adm_maint":
        CONFIG["maintenance_mode"] = not CONFIG["maintenance_mode"]
        db.set_setting("maintenance_mode", str(CONFIG["maintenance_mode"]))
        logger.info(f"Maintenance mode → {CONFIG['maintenance_mode']}")
        await _render_panel(update)
        return ADMIN_MENU

    # ── Full stats ─────────────────────────────────────────────────────────────
    if data == "adm_stats":
        stats = db.get_total_stats()
        active = stats["total_users"] - stats["total_banned"]
        sr = (stats["success_jobs"] / stats["total_jobs"] * 100
              if stats["total_jobs"] else 0.0)

        text = (
            "📊 *Full Statistics — ReFrame*\n\n"
            "*Users:*\n"
            f"  Total: `{stats['total_users']}`\n"
            f"  Active: `{active}`  |  Banned: `{stats['total_banned']}`\n\n"
            "*Media processed:*\n"
            f"  📸 Photos: `{stats['total_photos']}`\n"
            f"  🎬 Videos: `{stats['total_videos']}`\n"
            f"  Total jobs: `{stats['total_jobs']}`\n"
            f"  Success rate: `{sr:.1f}%`\n\n"
            "*Security:*\n"
            f"  🚫 Threats blocked: `{stats['total_threats']}`\n\n"
            "*Runtime config:*\n"
            f"  Max concurrent jobs: `{CONFIG['max_concurrent_jobs']}`\n"
            f"  Max file size: `{CONFIG['max_file_size_mb']} MB`\n"
            f"  Max resolution: `{CONFIG['max_resolution']}px`\n"
            f"  Video CRF: `{CONFIG['video_crf']}`\n"
            f"  Video preset: `{CONFIG['video_preset']}`\n"
            f"  Compress quality: `{CONFIG['compress_image_quality']}`\n"
            f"  Process timeout: `{CONFIG['process_timeout']}s`"
        )
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN
        )
        return ADMIN_MENU

    # ── Security logs ──────────────────────────────────────────────────────────
    if data == "adm_seclogs":
        rows = db.execute(
            "SELECT user_id, threat, timestamp FROM security_logs "
            "ORDER BY id DESC LIMIT 15",
            fetch_all=True,
        )
        if not rows:
            body = "_No security events recorded._"
        else:
            lines = []
            for r in rows:
                ts = (r["timestamp"] or "?")[:16]
                lines.append(f"👤 `{r['user_id']}` · {ts}\n⚠️ _{r['threat'][:80]}_")
            body = "\n\n".join(lines)

        text = f"🔒 *Security Logs (last 15)*\n\n{body}"
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN
        )
        return ADMIN_MENU

    # ── Settings sub-panel ─────────────────────────────────────────────────────
    if data == "adm_settings":
        text = (
            "⚙️ *Adjustable Settings*\n\n"
            "Send a command to change a value:\n\n"
            "`set_crf <0-51>` — video quality (lower=better, default 23)\n"
            "`set_preset <ultrafast|fast|medium|slow>` — encoding speed\n"
            "`set_quality <1-95>` — compress image quality\n"
            "`set_maxsize <MB>` — max upload size in MB\n\n"
            "_Example:_ `set_crf 20`"
        )
        kb = [[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]]
        await query.edit_message_text(
            text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN
        )
        context.user_data["adm_action"] = "settings"
        return ADMIN_INPUT

    # ── Back from ADMIN_INPUT state ───────────────────────────────────────────
    if data == "adm_back":
        context.user_data.pop("adm_action", None)
        await _render_panel(update)
        return ADMIN_MENU

    # ── Broadcast prompt ───────────────────────────────────────────────────────
    if data == "adm_cast":
        await query.edit_message_text(
            "📣 *Broadcast*\n\nType your message to send to *all* users.\n"
            "Supports Markdown. Send /cancel to abort.",
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["adm_action"] = "cast"
        return ADMIN_INPUT

    # ── Manage user prompt ─────────────────────────────────────────────────────
    if data == "adm_user":
        await query.edit_message_text(
            "👤 *Manage User*\n\nEnter the numeric Telegram *user ID*:",
            parse_mode=ParseMode.MARKDOWN,
        )
        context.user_data["adm_action"] = "user_lookup"
        return ADMIN_INPUT

    # ── Ban / Unban action ─────────────────────────────────────────────────────
    if data.startswith("ban_"):
        # format: ban_<0|1>_<user_id>
        parts = data.split("_", 2)
        if len(parts) != 3 or not parts[2].isdigit():
            await query.edit_message_text("❌ Invalid ban data.")
            return ADMIN_MENU

        is_ban = (parts[1] == "1")
        uid    = int(parts[2])
        db.set_ban_status(uid, is_ban)
        label  = "🛑 BANNED" if is_ban else "✅ UNBANNED"
        logger.info(f"Admin {update.effective_user.id} → user {uid} {label}")

        kb = [[InlineKeyboardButton("🔙 Back", callback_data="adm_back")]]
        await query.edit_message_text(
            f"✅ *Done* — User `{uid}` is now *{label}*.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.MARKDOWN,
        )
        return ADMIN_MENU

    # Fallback
    await _render_panel(update)
    return ADMIN_MENU


# ─────────────────────────────────────────────────────────────────────────────
# Admin text input  (ADMIN_INPUT state)
# ─────────────────────────────────────────────────────────────────────────────
async def admin_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not _is_admin(update):
        return ConversationHandler.END

    text   = (update.message.text or "").strip()
    action = context.user_data.get("adm_action", "")

    # ── Broadcast ──────────────────────────────────────────────────────────────
    if action == "cast":
        ids     = db.get_all_user_ids()
        sent    = 0
        failed  = 0
        prog    = await update.message.reply_text(
            f"🚀 *Broadcasting to {len(ids)} users…*\n\nSent: 0",
            parse_mode=ParseMode.MARKDOWN,
        )
        for i, uid in enumerate(ids):
            try:
                await context.bot.send_message(
                    uid,
                    f"📢 *Message from Admin*\n\n{text}",
                    parse_mode=ParseMode.MARKDOWN,
                )
                sent += 1
            except Forbidden:
                failed += 1
            except Exception as exc:
                failed += 1
                logger.error(f"Broadcast to {uid}: {exc}")

            if (i + 1) % 20 == 0:
                try:
                    await prog.edit_text(
                        f"🚀 *Broadcasting…*\n\nSent: {sent}  |  Failed: {failed}",
                        parse_mode=ParseMode.MARKDOWN,
                    )
                except Exception:
                    pass
            await asyncio.sleep(0.04)   # respect Telegram rate limit

        await prog.edit_text(
            f"✅ *Broadcast complete!*\n\n✓ Sent: {sent}  |  ✗ Failed: {failed}",
            parse_mode=ParseMode.MARKDOWN,
        )
        await _render_panel(update)
        return ADMIN_MENU

    # ── User lookup ────────────────────────────────────────────────────────────
    if action == "user_lookup":
        if not text.isdigit():
            await update.message.reply_text(
                "❌ *Invalid ID* — enter a numeric Telegram user ID.",
                parse_mode=ParseMode.MARKDOWN,
            )
            return ADMIN_INPUT

        uid = int(text)
        row = db.get_user(uid)
        if not row:
            await update.message.reply_text(
                "❌ *User not found* in database.",
                parse_mode=ParseMode.MARKDOWN,
            )
            await _render_panel(update)
            return ADMIN_MENU

        status = "🛑 BANNED" if row["is_banned"] else "✅ Active"
        total  = (row["photos_processed"] or 0) + (row["videos_processed"] or 0)
        info = (
            f"👤 *User Info*\n\n"
            f"🆔 ID: `{uid}`\n"
            f"👤 Name: {row['first_name'] or '—'}\n"
            f"📛 Username: @{row['username'] or '—'}\n"
            f"📅 Joined: {(row['joined_date'] or '?')[:10]}\n"
            f"🌐 Language: `{row['language'] or 'en'}`\n\n"
            f"📸 Photos: `{row['photos_processed'] or 0}`\n"
            f"🎬 Videos: `{row['videos_processed'] or 0}`\n"
            f"📦 Total: `{total}`\n\n"
            f"✨ Status: {status}"
        )
        kb = [
            [InlineKeyboardButton("🛑 Ban",   callback_data=f"ban_1_{uid}"),
             InlineKeyboardButton("✅ Unban", callback_data=f"ban_0_{uid}")],
            [InlineKeyboardButton("🔙 Back",  callback_data="adm_back")],
        ]
        await update.message.reply_text(
            info, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN
        )
        return ADMIN_MENU

    # ── Settings ───────────────────────────────────────────────────────────────
    if action == "settings":
        parts = text.split()
        ok    = False

        if len(parts) == 2:
            cmd, val = parts[0].lower(), parts[1]
            try:
                if cmd == "set_crf":
                    v = int(val)
                    assert 0 <= v <= 51
                    CONFIG["video_crf"] = v
                    db.set_setting("video_crf", v)
                    ok = True
                elif cmd == "set_preset":
                    assert val in ("ultrafast","superfast","veryfast","faster",
                                   "fast","medium","slow","slower","veryslow")
                    CONFIG["video_preset"] = val
                    db.set_setting("video_preset", val)
                    ok = True
                elif cmd == "set_quality":
                    v = int(val)
                    assert 1 <= v <= 95
                    CONFIG["compress_image_quality"] = v
                    db.set_setting("compress_image_quality", v)
                    ok = True
                elif cmd == "set_maxsize":
                    v = int(val)
                    assert 1 <= v <= 2000
                    CONFIG["max_file_size_mb"] = v
                    db.set_setting("max_file_size_mb", v)
                    ok = True
            except (ValueError, AssertionError):
                pass

        if ok:
            await update.message.reply_text(
                f"✅ *Setting updated:* `{text}`", parse_mode=ParseMode.MARKDOWN
            )
        else:
            await update.message.reply_text(
                "❌ *Unknown command or invalid value.*\n\nSee the settings panel for syntax.",
                parse_mode=ParseMode.MARKDOWN,
            )
        await _render_panel(update)
        return ADMIN_MENU

    # Fallback
    await _render_panel(update)
    return ADMIN_MENU
