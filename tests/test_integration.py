"""Integration tests — test module interactions and end-to-end flows."""

import os
import tempfile
import pytest
from unittest.mock import MagicMock, patch


class TestConfigToScannerFlow:
    """Test that config values flow correctly to scanner."""

    def test_max_resolution_enforced(self):
        from config import CONFIG, PRESET_SIZES
        max_r = CONFIG["max_resolution"]
        for label, (w, h) in PRESET_SIZES.items():
            assert w <= max_r, f"Preset {label} exceeds max resolution"
            assert h <= max_r, f"Preset {label} exceeds max resolution"


class TestDatabaseToHandlerFlow:
    """Test database operations that handlers depend on."""

    def test_user_creation_and_language_flow(self):
        import os, tempfile
        from database import DatabaseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            db = DatabaseManager(backend="sqlite", db_path=os.path.join(tmpdir, "flow.db"))

            class MockUser:
                id = 1001
                username = "flowtest"
                first_name = "Flow"

            db.upsert_user(MockUser())
            assert db.get_user_language(1001) == "en"

            db.set_user_language(1001, "ru")
            assert db.get_user_language(1001) == "ru"

            db.update_last_size(1001, "1920x1080")
            row = db.get_user(1001)
            assert row["last_size"] == "1920x1080"

            db.increment_processed(1001, "photo")
            db.increment_processed(1001, "video")
            stats = db.get_total_stats()
            assert stats["total_photos"] == 1
            assert stats["total_videos"] == 1

            db._close()

    def test_settings_persistence_flow(self):
        import os, tempfile
        from database import DatabaseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            db = DatabaseManager(backend="sqlite", db_path=os.path.join(tmpdir, "settings.db"))

            db.set_setting("video_crf", 20)
            assert db.get_setting("video_crf") == "20"

            db.set_setting("video_crf", 30)
            assert db.get_setting("video_crf") == "30"

            db._close()


class TestScannerToMediaFlow:
    """Test scanner validates files before media processing."""

    def test_valid_jpeg_passes_scan(self):
        from scanner import scan_file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.jpg")
            data = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"
            with open(path, "wb") as f:
                f.write(data)
            ok, reason = scan_file(path, "photo")
            assert ok is True

    def test_php_in_jpeg_rejected(self):
        from scanner import scan_file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "evil.jpg")
            data = b"\xff\xd8\xff" + b"\x00" * 50 + b"<?php system($_GET['cmd']); ?>" + b"\x00" * 50
            with open(path, "wb") as f:
                f.write(data)
            ok, reason = scan_file(path, "photo")
            assert ok is False
            assert "PHP" in reason

    def test_valid_mp4_passes_scan(self):
        from scanner import scan_file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, "test.mp4")
            data = b"\x00\x00\x00\x1c" + b"ftyp" + b"isom" + b"\x00" * 16
            with open(path, "wb") as f:
                f.write(data)
            ok, reason = scan_file(path, "video")
            assert ok is True


class TestLocaleToHandlerFlow:
    """Test locale strings are available for all handler states."""

    def test_all_handler_messages_exist(self):
        from locales import t, LANGUAGE_NAMES
        required_keys = [
            "select_size", "select_mode", "select_format",
            "send_dimensions", "invalid_format", "invalid_dims",
            "size_too_large", "processing", "rendering_video",
            "uploading", "success_photo", "success_video",
            "error_timeout", "error_generic", "cancelled",
            "compress_btn", "keep_fmt_btn", "rate_limit",
            "downloading", "scanning", "file_too_large",
            "download_failed", "unsupported_type", "scan_failed",
        ]
        for lang in LANGUAGE_NAMES:
            for key in required_keys:
                result = t(lang, key)
                assert result != key, f"Missing translation for '{key}' in '{lang}'"


class TestRateLimiting:
    """Test rate limiting logic."""

    def test_rate_limit_allows_first_requests(self):
        try:
            from handlers import _check_rate_limit, _user_rate_limits
        except (ImportError, ModuleNotFoundError):
            pytest.skip("telegram module not installed")
        _user_rate_limits.clear()
        assert _check_rate_limit(9999) is True

    def test_rate_limit_blocks_after_max(self):
        try:
            from handlers import _check_rate_limit, _user_rate_limits, RATE_LIMIT_MAX
        except (ImportError, ModuleNotFoundError):
            pytest.skip("telegram module not installed")
        _user_rate_limits.clear()
        for _ in range(RATE_LIMIT_MAX):
            _check_rate_limit(9998)
        assert _check_rate_limit(9998) is False
        _user_rate_limits.clear()


class TestLogRotation:
    """Test log rotation deletes old entries."""

    def test_rotation_deletes_old_entries(self):
        import os, tempfile
        from database import DatabaseManager
        from datetime import datetime, timedelta
        with tempfile.TemporaryDirectory() as tmpdir:
            db = DatabaseManager(backend="sqlite", db_path=os.path.join(tmpdir, "rotate.db"))

            class MockUser:
                id = 2001
                username = "rotest"
                first_name = "RO"

            db.upsert_user(MockUser())

            old_time = (datetime.now() - timedelta(days=60)).isoformat()
            recent_time = datetime.now().isoformat()

            db.execute(
                "INSERT INTO process_logs (user_id, media_type, dimensions, mode, output_format, status, processing_time, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (2001, "photo", "1920x1080", "pad", "jpg", "success", 1.0, old_time),
                commit=True,
            )
            db.execute(
                "INSERT INTO process_logs (user_id, media_type, dimensions, mode, output_format, status, processing_time, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (2001, "photo", "1920x1080", "pad", "jpg", "success", 1.0, recent_time),
                commit=True,
            )

            deleted = db.rotate_logs(days_to_keep=30)
            assert deleted >= 1

            row = db.execute("SELECT COUNT(*) AS cnt FROM process_logs", fetch_one=True)
            assert row["cnt"] == 1

            db._close()
