"""
locales.py 
All user-facing strings in 4 languages: English, Russian, Chinese, Persian.
Helper function t(lang, key, **kwargs) returns the localised string.
"""

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ── Language metadata ──────────────────────────────────────────────────────────
LANGUAGE_NAMES: dict[str, str] = {
    "en": "🇺🇸 English",
    "ru": "🇷🇺 Русский",
    "zh": "🇨🇳 中文",
    "fa": "🇮🇷 فارسی",
}

# ── String table ───────────────────────────────────────────────────────────────
STRINGS: dict[str, dict[str, str]] = {

    # ── ENGLISH ───────────────────────────────────────────────────────────────
    "en": {
        "choose_language": "🌐 *Please choose your language:*",
        "language_set":    "✅ Language set to *English*!",

        "welcome": (
            "👋 *Welcome, {name}!*\n\n"
            "🦉 *Reframe* — your media processing bot.\n\n"
            "📸 I can *resize*, *compress*, and *convert* your Photos & Videos.\n\n"
            "📌 *How to use:*\n"
            "1. Send me a photo or video\n"
            "2. Pick a preset size, Compress, or enter custom dimensions\n"
            "3. Choose resize mode (Fit / Stretch)\n"
            "4. Choose output format (optional)\n"
            "5. Receive your processed file!\n\n"
            "💡 */help* – full guide  |  */stats* – your usage  |  */lang* – change language"
        ),

        "help_text": (
            "📚 *Reframe — Help Guide*\n\n"
            "*Supported input formats:*\n"
            "• Photos: JPG, PNG, WEBP, GIF, BMP\n"
            "• Videos: MP4, MOV, AVI, MKV, WEBM\n\n"
            "*Preset sizes:*\n"
            "• Instagram Post: 1080×1080\n"
            "• Instagram Story: 1080×1920\n"
            "• HD: 1280×720  |  Full HD: 1920×1080\n"
            "• 4K: 3840×2160\n"
            "• Twitter: 1200×675  |  Facebook: 820×312\n\n"
            "*Resize modes:*\n"
            "🎯 *Fit* — keeps ratio, adds black bars\n"
            "🔲 *Stretch* — exact size, may distort\n\n"
            "*Format conversion:*\n"
            "• Photos → JPG / PNG / WEBP\n"
            "• Videos → MP4 / AVI / MKV\n\n"
            "🗜️ *Compress* — shrinks file without resizing\n\n"
            "*Custom dimensions:* send `1920x1080`\n\n"
            "*Limits:* 50 MB max · 3840 px max · 10 min timeout\n\n"
            "*Commands:*\n"
            "/start /help /stats /cancel /lang"
        ),

        "stats_text": (
            "📊 *Your Statistics*\n\n"
            "👤 *User:* {name}\n"
            "📅 *Joined:* {joined}\n\n"
            "📸 *Photos processed:* {photos}\n"
            "🎬 *Videos processed:* {videos}\n"
            "📦 *Total files:* {total}\n\n"
            "⏱ *Total processing time:* {time}s\n"
            "📏 *Last size used:* {last_size}\n\n"
            "✨ *Status:* {status}"
        ),

        "maintenance":      "🚧 *Maintenance mode is ON.* Please try again later.",
        "banned":           "🛑 *You are banned from using this bot.*",
        "processing_wait":  "⏳ Please wait for your current file to finish.",
        "downloading":      "⬇️ *Downloading…*",
        "scanning":         "🔍 *Scanning file for threats…*",
        "processing":       "⚙️ *Processing…*",
        "rendering_video":  "🎞 *Rendering video…*\n\n⏳ This may take a few minutes.",
        "uploading":        "⬆️ *Uploading…*",

        "file_too_large":   "❌ *File too large!*\n\nMax: {max_mb} MB · Your file: {file_mb:.1f} MB",
        "download_failed":  "❌ *Download failed!*\n\n`{error}`",
        "unsupported_type": "❌ *Unsupported file type.*\nSend an *Image* or *Video*.",
        "scan_failed":      "🚫 *Security Alert!*\n\n_{reason}_\n\nFile rejected for safety.",
        "cancelled":        "❌ *Cancelled.*",
        "no_stats":         "❌ No stats yet — process some media first!",
        "access_denied":    "❌ *Access denied.*",

        "error_timeout":    (
            "❌ *Processing timeout!*\n\n"
            "The file took too long. Try a smaller file or lower resolution."
        ),
        "error_generic":    "❌ *Processing error!*\n\n`{error}`",

        "select_size":      "📐 *Select a size or action:*",
        "select_mode":      (
            "🎨 *Select resize mode:*\n\n"
            "🎯 *Fit* — keeps aspect ratio (adds black bars)\n"
            "🔲 *Stretch* — exact size (may distort image)"
        ),
        "select_format":    "🔄 *Select output format:*",
        "send_dimensions":  "✍️ *Enter custom dimensions*\n\nFormat: `WIDTHxHEIGHT`\nExample: `1920x1080`",
        "invalid_format":   "❌ *Invalid format!*\n\nUse: `WIDTHxHEIGHT`  e.g. `1920x1080`",
        "invalid_dims":     "❌ *Invalid dimensions!*\nWidth and height must be positive integers.",
        "size_too_large":   "❌ *Size too large!*\n\nMax: {max_res}px · Requested: {your_res}px",

        "success_photo": "✅ Processed → *{size}* | Mode: {mode} | Format: {fmt}\n⏱ {time:.1f}s",
        "success_video": (
            "✅ Processed → *{size}* | Mode: {mode} | Format: {fmt}\n"
            "⏱ {time:.1f}s · 📦 {file_mb:.1f} MB"
        ),

        "compress_btn":  "🗜️ Compress (reduce size)",
        "last_size_btn": "↺ Last used ({size})",
        "custom_btn":    "✏️ Custom size",
        "cancel_btn":    "❌ Cancel",
        "fit_btn":       "🎯 Fit (Pad)",
        "stretch_btn":   "🔲 Stretch",
        "keep_fmt_btn":  "✅ Keep original",
        "rate_limit":    "🚫 *Rate limit exceeded.*\nPlease wait a moment before sending another file.",
    },

    # ── RUSSIAN ───────────────────────────────────────────────────────────────
    "ru": {
        "choose_language": "🌐 *Пожалуйста, выберите язык:*",
        "language_set":    "✅ Язык установлен: *Русский*!",

        "welcome": (
            "👋 *Добро пожаловать, {name}!*\n\n"
            "🦉 *Reframe* — ваш бот для обработки медиа.\n\n"
            "📸 Я умею *изменять размер*, *сжимать* и *конвертировать* фото и видео.\n\n"
            "📌 *Как пользоваться:*\n"
            "1. Отправьте фото или видео\n"
            "2. Выберите размер, сжатие или введите свои размеры\n"
            "3. Выберите режим (Вписать / Растянуть)\n"
            "4. Выберите формат (опционально)\n"
            "5. Получите обработанный файл!\n\n"
            "💡 */help* – справка  |  */stats* – статистика  |  */lang* – язык"
        ),

        "help_text": (
            "📚 *Reframe — Руководство*\n\n"
            "*Поддерживаемые форматы:*\n"
            "• Фото: JPG, PNG, WEBP, GIF, BMP\n"
            "• Видео: MP4, MOV, AVI, MKV, WEBM\n\n"
            "*Режимы:*\n"
            "🎯 *Вписать* — сохраняет пропорции, добавляет полосы\n"
            "🔲 *Растянуть* — точный размер, возможно искажение\n\n"
            "*Форматы вывода:*\n"
            "• Фото → JPG / PNG / WEBP\n"
            "• Видео → MP4 / AVI / MKV\n\n"
            "🗜️ *Сжать* — уменьшает файл без изменения размера\n\n"
            "*Команды:* /start /help /stats /cancel /lang"
        ),

        "stats_text": (
            "📊 *Ваша статистика*\n\n"
            "👤 *Пользователь:* {name}\n"
            "📅 *Дата регистрации:* {joined}\n\n"
            "📸 *Обработано фото:* {photos}\n"
            "🎬 *Обработано видео:* {videos}\n"
            "📦 *Всего файлов:* {total}\n\n"
            "⏱ *Общее время обработки:* {time}с\n"
            "📏 *Последний размер:* {last_size}\n\n"
            "✨ *Статус:* {status}"
        ),

        "maintenance":      "🚧 *Режим обслуживания включён.* Попробуйте позже.",
        "banned":           "🛑 *Вы заблокированы в этом боте.*",
        "processing_wait":  "⏳ Подождите завершения обработки текущего файла.",
        "downloading":      "⬇️ *Загрузка…*",
        "scanning":         "🔍 *Сканирование файла на угрозы…*",
        "processing":       "⚙️ *Обработка…*",
        "rendering_video":  "🎞 *Рендеринг видео…*\n\n⏳ Это может занять несколько минут.",
        "uploading":        "⬆️ *Загрузка…*",

        "file_too_large":   "❌ *Файл слишком большой!*\n\nМакс: {max_mb} МБ · Ваш файл: {file_mb:.1f} МБ",
        "download_failed":  "❌ *Ошибка загрузки!*\n\n`{error}`",
        "unsupported_type": "❌ *Неподдерживаемый тип файла.*\nОтправьте *Изображение* или *Видео*.",
        "scan_failed":      "🚫 *Угроза безопасности!*\n\n_{reason}_\n\nФайл отклонён.",
        "cancelled":        "❌ *Отменено.*",
        "no_stats":         "❌ Статистика не найдена. Сначала обработайте файл!",
        "access_denied":    "❌ *Доступ запрещён.*",

        "error_timeout":    "❌ *Время ожидания истекло!*\n\nПопробуйте файл меньшего размера.",
        "error_generic":    "❌ *Ошибка обработки!*\n\n`{error}`",

        "select_size":      "📐 *Выберите размер или действие:*",
        "select_mode":      (
            "🎨 *Выберите режим изменения размера:*\n\n"
            "🎯 *Вписать* — сохраняет пропорции (добавляет полосы)\n"
            "🔲 *Растянуть* — точный размер (возможно искажение)"
        ),
        "select_format":    "🔄 *Выберите формат вывода:*",
        "send_dimensions":  "✍️ *Введите размеры*\n\nФормат: `ШИРИНАxВЫСОТА`\nПример: `1920x1080`",
        "invalid_format":   "❌ *Неверный формат!*\n\nИспользуйте: `ШИРИНАxВЫСОТА`",
        "invalid_dims":     "❌ *Неверные размеры!*\nШирина и высота должны быть положительными.",
        "size_too_large":   "❌ *Размер слишком большой!*\n\nМакс: {max_res}px · Запрошено: {your_res}px",

        "success_photo": "✅ Обработано → *{size}* | Режим: {mode} | Формат: {fmt}\n⏱ {time:.1f}с",
        "success_video": "✅ Обработано → *{size}* | Режим: {mode} | Формат: {fmt}\n⏱ {time:.1f}с · 📦 {file_mb:.1f} МБ",

        "compress_btn":  "🗜️ Сжать (уменьшить размер)",
        "last_size_btn": "↺ Последний ({size})",
        "custom_btn":    "✏️ Свой размер",
        "cancel_btn":    "❌ Отмена",
        "fit_btn":       "🎯 Вписать",
        "stretch_btn":   "🔲 Растянуть",
        "keep_fmt_btn":  "✅ Оставить оригинал",
        "rate_limit":    "🚫 *Превышен лимит запросов.*\nПодождите немного перед отправкой следующего файла.",
    },

    # ── CHINESE ───────────────────────────────────────────────────────────────
    "zh": {
        "choose_language": "🌐 *请选择您的语言：*",
        "language_set":    "✅ 语言已设置为*中文*！",

        "welcome": (
            "👋 *欢迎，{name}！*\n\n"
            "🦉 *Reframe* — 您的媒体处理机器人。\n\n"
            "📸 我可以*调整大小*、*压缩*和*转换*您的照片和视频。\n\n"
            "📌 *使用方法：*\n"
            "1. 发送照片或视频\n"
            "2. 选择预设尺寸、压缩或自定义尺寸\n"
            "3. 选择调整模式（适应/拉伸）\n"
            "4. 选择输出格式（可选）\n"
            "5. 接收处理后的文件！\n\n"
            "💡 */help* – 帮助  |  */stats* – 统计  |  */lang* – 语言"
        ),

        "help_text": (
            "📚 *Reframe — 使用指南*\n\n"
            "*支持格式：*\n"
            "• 照片：JPG, PNG, WEBP, GIF, BMP\n"
            "• 视频：MP4, MOV, AVI, MKV, WEBM\n\n"
            "*调整模式：*\n"
            "🎯 *适应* — 保持比例，添加黑边\n"
            "🔲 *拉伸* — 精确尺寸，可能变形\n\n"
            "*输出格式：*\n"
            "• 照片 → JPG / PNG / WEBP\n"
            "• 视频 → MP4 / AVI / MKV\n\n"
            "🗜️ *压缩* — 减小文件大小，不改变分辨率\n\n"
            "*命令：* /start /help /stats /cancel /lang"
        ),

        "stats_text": (
            "📊 *您的统计信息*\n\n"
            "👤 *用户：* {name}\n"
            "📅 *加入日期：* {joined}\n\n"
            "📸 *处理照片：* {photos}\n"
            "🎬 *处理视频：* {videos}\n"
            "📦 *总文件数：* {total}\n\n"
            "⏱ *总处理时间：* {time}秒\n"
            "📏 *上次尺寸：* {last_size}\n\n"
            "✨ *状态：* {status}"
        ),

        "maintenance":      "🚧 *维护模式已开启。* 请稍后再试。",
        "banned":           "🛑 *您已被封禁，无法使用此机器人。*",
        "processing_wait":  "⏳ 请等待当前文件处理完成。",
        "downloading":      "⬇️ *下载中…*",
        "scanning":         "🔍 *正在扫描文件威胁…*",
        "processing":       "⚙️ *处理中…*",
        "rendering_video":  "🎞 *渲染视频中…*\n\n⏳ 这可能需要几分钟。",
        "uploading":        "⬆️ *上传中…*",

        "file_too_large":   "❌ *文件太大！*\n\n最大：{max_mb} MB · 您的文件：{file_mb:.1f} MB",
        "download_failed":  "❌ *下载失败！*\n\n`{error}`",
        "unsupported_type": "❌ *不支持的文件类型。*\n请发送*图片*或*视频*。",
        "scan_failed":      "🚫 *安全警告！*\n\n_{reason}_\n\n文件因安全原因被拒绝。",
        "cancelled":        "❌ *已取消。*",
        "no_stats":         "❌ 未找到统计信息。请先处理一些媒体！",
        "access_denied":    "❌ *访问被拒绝。*",

        "error_timeout":    "❌ *处理超时！*\n\n请尝试较小的文件或较低分辨率。",
        "error_generic":    "❌ *处理错误！*\n\n`{error}`",

        "select_size":      "📐 *选择尺寸或操作：*",
        "select_mode":      "🎨 *选择调整模式：*\n\n🎯 *适应* — 保持比例（添加黑边）\n🔲 *拉伸* — 精确尺寸（可能变形）",
        "select_format":    "🔄 *选择输出格式：*",
        "send_dimensions":  "✍️ *输入自定义尺寸*\n\n格式：`宽x高`\n示例：`1920x1080`",
        "invalid_format":   "❌ *格式无效！*\n\n请使用：`宽x高`",
        "invalid_dims":     "❌ *尺寸无效！*\n宽度和高度必须为正整数。",
        "size_too_large":   "❌ *尺寸过大！*\n\n最大：{max_res}px · 您的请求：{your_res}px",

        "success_photo": "✅ 已处理 → *{size}* | 模式：{mode} | 格式：{fmt}\n⏱ {time:.1f}秒",
        "success_video": "✅ 已处理 → *{size}* | 模式：{mode} | 格式：{fmt}\n⏱ {time:.1f}秒 · 📦 {file_mb:.1f} MB",

        "compress_btn":  "🗜️ 压缩（减小文件大小）",
        "last_size_btn": "↺ 上次使用 ({size})",
        "custom_btn":    "✏️ 自定义尺寸",
        "cancel_btn":    "❌ 取消",
        "fit_btn":       "🎯 适应",
        "stretch_btn":   "🔲 拉伸",
        "keep_fmt_btn":  "✅ 保持原格式",
        "rate_limit":    "🚫 *超出速率限制。*\n请稍等片刻再发送另一个文件。",
    },

    # ── PERSIAN / FARSI ───────────────────────────────────────────────────────
    "fa": {
        "choose_language": "🌐 *لطفاً زبان خود را انتخاب کنید:*",
        "language_set":    "✅ زبان به *فارسی* تنظیم شد!",

        "welcome": (
            "👋 *خوش آمدید، {name}!*\n\n"
            "🦉 *Reframe* — ربات پردازش رسانه شما.\n\n"
            "📸 می‌توانم عکس‌ها و ویدیوهای شما را *تغییر اندازه*، *فشرده* و *تبدیل فرمت* کنم.\n\n"
            "📌 *نحوه استفاده:*\n"
            "1. عکس یا ویدیو ارسال کنید\n"
            "2. اندازه، فشرده‌سازی یا ابعاد دلخواه انتخاب کنید\n"
            "3. حالت تغییر اندازه انتخاب کنید (جا دادن / کشیدن)\n"
            "4. فرمت خروجی انتخاب کنید (اختیاری)\n"
            "5. فایل پردازش‌شده را دریافت کنید!\n\n"
            "💡 */help* – راهنما  |  */stats* – آمار  |  */lang* – زبان"
        ),

        "help_text": (
            "📚 *Reframe — راهنمای کامل*\n\n"
            "*فرمت‌های پشتیبانی‌شده:*\n"
            "• عکس: JPG، PNG، WEBP، GIF، BMP\n"
            "• ویدیو: MP4، MOV، AVI، MKV، WEBM\n\n"
            "*حالت‌های تغییر اندازه:*\n"
            "🎯 *جا دادن* — حفظ نسبت، افزودن حاشیه\n"
            "🔲 *کشیدن* — اندازه دقیق، احتمال تغییر شکل\n\n"
            "*تبدیل فرمت:*\n"
            "• عکس → JPG / PNG / WEBP\n"
            "• ویدیو → MP4 / AVI / MKV\n\n"
            "🗜️ *فشرده‌سازی* — کاهش حجم بدون تغییر اندازه\n\n"
            "*دستورات:* /start /help /stats /cancel /lang"
        ),

        "stats_text": (
            "📊 *آمار شما*\n\n"
            "👤 *کاربر:* {name}\n"
            "📅 *تاریخ عضویت:* {joined}\n\n"
            "📸 *عکس‌های پردازش‌شده:* {photos}\n"
            "🎬 *ویدیوهای پردازش‌شده:* {videos}\n"
            "📦 *مجموع فایل‌ها:* {total}\n\n"
            "⏱ *کل زمان پردازش:* {time} ثانیه\n"
            "📏 *آخرین اندازه:* {last_size}\n\n"
            "✨ *وضعیت:* {status}"
        ),

        "maintenance":      "🚧 *حالت تعمیر فعال است.* لطفاً بعداً امتحان کنید.",
        "banned":           "🛑 *شما از استفاده از این ربات مسدود شده‌اید.*",
        "processing_wait":  "⏳ لطفاً صبر کنید تا پردازش فایل فعلی تمام شود.",
        "downloading":      "⬇️ *در حال دانلود…*",
        "scanning":         "🔍 *در حال اسکن فایل برای تهدیدات…*",
        "processing":       "⚙️ *در حال پردازش…*",
        "rendering_video":  "🎞 *در حال رندر ویدیو…*\n\n⏳ این ممکن است چند دقیقه طول بکشد.",
        "uploading":        "⬆️ *در حال آپلود…*",

        "file_too_large":   "❌ *فایل خیلی بزرگ است!*\n\nحداکثر: {max_mb} مگابایت · فایل شما: {file_mb:.1f} مگابایت",
        "download_failed":  "❌ *دانلود ناموفق!*\n\n`{error}`",
        "unsupported_type": "❌ *نوع فایل پشتیبانی نمی‌شود.*\nلطفاً یک *تصویر* یا *ویدیو* ارسال کنید.",
        "scan_failed":      "🚫 *هشدار امنیتی!*\n\n_{reason}_\n\nفایل به دلایل امنیتی رد شد.",
        "cancelled":        "❌ *لغو شد.*",
        "no_stats":         "❌ آماری یافت نشد. ابتدا یک فایل پردازش کنید!",
        "access_denied":    "❌ *دسترسی رد شد.*",

        "error_timeout":    "❌ *زمان پردازش به پایان رسید!*\n\nفایل کوچکتر یا رزولوشن پایین‌تر را امتحان کنید.",
        "error_generic":    "❌ *خطای پردازش!*\n\n`{error}`",

        "select_size":      "📐 *اندازه یا عملیات را انتخاب کنید:*",
        "select_mode":      "🎨 *حالت تغییر اندازه را انتخاب کنید:*\n\n🎯 *جا دادن* — حفظ نسبت (افزودن حاشیه)\n🔲 *کشیدن* — اندازه دقیق (احتمال تغییر شکل)",
        "select_format":    "🔄 *فرمت خروجی را انتخاب کنید:*",
        "send_dimensions":  "✍️ *ابعاد دلخواه را وارد کنید*\n\nفرمت: `عرضxارتفاع`\nمثال: `1920x1080`",
        "invalid_format":   "❌ *فرمت نامعتبر!*\n\nاستفاده کنید: `عرضxارتفاع`",
        "invalid_dims":     "❌ *ابعاد نامعتبر!*\nعرض و ارتفاع باید اعداد مثبت باشند.",
        "size_too_large":   "❌ *اندازه خیلی بزرگ است!*\n\nحداکثر: {max_res}px · درخواست شما: {your_res}px",

        "success_photo": "✅ پردازش شد → *{size}* | حالت: {mode} | فرمت: {fmt}\n⏱ {time:.1f} ثانیه",
        "success_video": "✅ پردازش شد → *{size}* | حالت: {mode} | فرمت: {fmt}\n⏱ {time:.1f} ثانیه · 📦 {file_mb:.1f} مگابایت",

        "compress_btn":  "🗜️ فشرده‌سازی (کاهش حجم)",
        "last_size_btn": "↺ آخرین ({size})",
        "custom_btn":    "✏️ اندازه دلخواه",
        "cancel_btn":    "❌ لغو",
        "fit_btn":       "🎯 جا دادن",
        "stretch_btn":   "🔲 کشیدن",
        "keep_fmt_btn":  "✅ حفظ فرمت اصلی",
        "rate_limit":    "🚫 *محدودیت سرعت رد شد.*\nلطفاً قبل از ارسال فایل بعدی کمی صبر کنید.",
    },
}


# ── Helper ─────────────────────────────────────────────────────────────────────
def t(lang: str, key: str, **kwargs: Any) -> str:
    """Return localised string for *lang* and *key*, formatted with kwargs."""
    lang = lang if lang in STRINGS else "en"
    text = STRINGS[lang].get(key) or STRINGS["en"].get(key) or key
    if kwargs:
        try:
            text = text.format(**kwargs)
        except (KeyError, ValueError) as exc:
            logger.warning(f"Locale format error: lang={lang} key={key} error={exc}")
    return text
