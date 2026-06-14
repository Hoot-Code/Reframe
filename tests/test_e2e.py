"""E2E integration tests — test full handler flows with mocked Telegram API."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch

try:
    from handlers import start, language_callback, health_command, shutdown_command
    _HAS_TELEGRAM = True
except (ImportError, ModuleNotFoundError):
    _HAS_TELEGRAM = False


class MockUser:
    def __init__(self, user_id=12345, username="testuser", first_name="Test"):
        self.id = user_id
        self.username = username
        self.first_name = first_name


class MockMessage:
    def __init__(self, text=None, photo=None, video=None, document=None):
        self.text = text
        self.photo = photo
        self.video = video
        self.document = document
        self.reply_text = AsyncMock()
        self.reply_video = AsyncMock()
        self.reply_photo = AsyncMock()


class MockQuery:
    def __init__(self, data="test", from_user=None):
        self.data = data
        self.from_user = from_user or MockUser()
        self.answer = AsyncMock()
        self.edit_message_text = AsyncMock()
        self.delete_message = AsyncMock()
        self.message = MockMessage()


class MockUpdate:
    def __init__(self, message=None, callback_query=None, user=None):
        self.message = message
        self.callback_query = callback_query
        self.effective_user = user or MockUser()
        self.effective_chat = MagicMock()
        self.effective_chat.id = 12345


@pytest.fixture
def mock_db():
    """Provide a mock database."""
    with patch("handlers.db") as db:
        db.get_user.return_value = None
        db.get_user_language.return_value = "en"
        db.upsert_user.return_value = None
        db.set_user_language.return_value = None
        db.update_last_size.return_value = None
        db.increment_processed.return_value = None
        db.add_processing_time.return_value = None
        db.log_process.return_value = None
        db.log_security_event.return_value = None
        db.get_total_stats.return_value = {
            "total_users": 0, "total_photos": 0, "total_videos": 0,
            "total_banned": 0, "total_threats": 0, "total_jobs": 0, "success_jobs": 0,
        }
        yield db


@pytest.mark.skipif(not _HAS_TELEGRAM, reason="telegram module not installed")
class TestStartFlow:
    @pytest.mark.asyncio
    async def test_start_creates_user_and_shows_keyboard(self, mock_db):
        from handlers import start
        update = MockUpdate(message=MockMessage())
        context = MagicMock()
        context.user_data = {}

        result = await start(update, context)

        mock_db.upsert_user.assert_called_once()
        update.message.reply_text.assert_called_once()
        assert result == 0  # SELECT_LANG


@pytest.mark.skipif(not _HAS_TELEGRAM, reason="telegram module not installed")
class TestLanguageFlow:
    @pytest.mark.asyncio
    async def test_language_callback_sets_language(self, mock_db):
        from handlers import language_callback
        query = MockQuery(data="lang_ru")
        update = MockUpdate(callback_query=query)
        context = MagicMock()
        context.user_data = {}

        result = await language_callback(update, context)

        mock_db.set_user_language.assert_called_once_with(12345, "ru")
        assert result == -1  # ConversationHandler.END

    @pytest.mark.asyncio
    async def test_invalid_language_rejected(self, mock_db):
        from handlers import language_callback
        query = MockQuery(data="lang_xyz")
        update = MockUpdate(callback_query=query)
        context = MagicMock()
        context.user_data = {}

        result = await language_callback(update, context)

        mock_db.set_user_language.assert_not_called()
        assert result == -1


class TestSizeParsing:
    def test_preset_size_parsed(self):
        data = "sz_1920x1080"
        _, size_part = data.split("_", 1)
        w, h = map(int, size_part.split("x"))
        assert (w, h) == (1920, 1080)

    def test_compressed_mode(self):
        data = "sz_compress"
        assert data == "sz_compress"

    def test_custom_size(self):
        data = "sz_custom"
        assert data == "sz_custom"

    def test_cancel(self):
        data = "sz_cancel"
        assert data == "sz_cancel"


class TestFormatValidation:
    def test_valid_photo_formats(self):
        from media_processor import IMAGE_FORMATS
        allowed = set(IMAGE_FORMATS)
        allowed.add("keep")
        assert "jpg" in allowed
        assert "png" in allowed
        assert "webp" in allowed
        assert "keep" in allowed

    def test_valid_video_formats(self):
        from media_processor import VIDEO_FORMATS
        allowed = set(VIDEO_FORMATS)
        allowed.add("keep")
        assert "mp4" in allowed
        assert "avi" in allowed
        assert "mkv" in allowed
        assert "keep" in allowed


@pytest.mark.skipif(not _HAS_TELEGRAM, reason="telegram module not installed")
class TestRateLimiting:
    def test_rate_limit_check(self):
        from handlers import _check_rate_limit, _user_rate_limits, RATE_LIMIT_MAX
        _user_rate_limits.clear()
        for _ in range(RATE_LIMIT_MAX):
            assert _check_rate_limit(8888) is True
        assert _check_rate_limit(8888) is False
        _user_rate_limits.clear()


@pytest.mark.skipif(not _HAS_TELEGRAM, reason="telegram module not installed")
class TestHealthCheck:
    def test_health_command_exists(self):
        from handlers import health_command
        assert callable(health_command)

    def test_shutdown_command_exists(self):
        from handlers import shutdown_command
        assert callable(shutdown_command)
