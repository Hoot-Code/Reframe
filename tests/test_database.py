"""Tests for database.py — user preferences and data persistence."""

import os
import tempfile
import pytest
from database import DatabaseManager


@pytest.fixture
def db():
    """Create a fresh in-memory database for each test."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = os.path.join(tmpdir, "test.db")
        manager = DatabaseManager(db_path)
        yield manager
        manager._close()


class MockUser:
    """Minimal user object for testing."""
    def __init__(self, user_id, username=None, first_name=None):
        self.id = user_id
        self.username = username
        self.first_name = first_name


class TestUserOperations:
    def test_upsert_new_user(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        row = db.get_user(123)
        assert row is not None
        assert row["user_id"] == 123
        assert row["username"] == "testuser"
        assert row["first_name"] == "Test"

    def test_upsert_existing_user_updates_name(self, db):
        user1 = MockUser(123, "testuser", "Old Name")
        db.upsert_user(user1)
        user2 = MockUser(123, "testuser", "New Name")
        db.upsert_user(user2)
        row = db.get_user(123)
        assert row["first_name"] == "New Name"

    def test_get_nonexistent_user(self, db):
        row = db.get_user(999)
        assert row is None

    def test_set_ban_status(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.set_ban_status(123, True)
        row = db.get_user(123)
        assert row["is_banned"] == 1

    def test_unban_user(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.set_ban_status(123, True)
        db.set_ban_status(123, False)
        row = db.get_user(123)
        assert row["is_banned"] == 0


class TestLanguagePreferences:
    def test_default_language(self, db):
        lang = db.get_user_language(999)
        assert lang == "en"

    def test_set_language(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.set_user_language(123, "ru")
        lang = db.get_user_language(123)
        assert lang == "ru"

    def test_set_language_all_codes(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        for lang_code in ["en", "ru", "zh", "fa"]:
            db.set_user_language(123, lang_code)
            assert db.get_user_language(123) == lang_code


class TestLastSize:
    def test_update_last_size(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.update_last_size(123, "1920x1080")
        row = db.get_user(123)
        assert row["last_size"] == "1920x1080"

    def test_update_compressed_mode(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.update_last_size(123, "compressed")
        row = db.get_user(123)
        assert row["last_size"] == "compressed"

    def test_last_size_none_by_default(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        row = db.get_user(123)
        assert row["last_size"] is None


class TestSettings:
    def test_set_and_get_setting(self, db):
        db.set_setting("video_crf", 20)
        val = db.get_setting("video_crf")
        assert val == "20"

    def test_overwrite_setting(self, db):
        db.set_setting("video_crf", 20)
        db.set_setting("video_crf", 30)
        val = db.get_setting("video_crf")
        assert val == "30"

    def test_get_nonexistent_setting(self, db):
        val = db.get_setting("nonexistent")
        assert val is None


class TestProcessLogs:
    def test_log_process(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.log_process(123, "photo", "1920x1080", "pad", "jpg", "success", 1.5)
        stats = db.get_total_stats()
        assert stats["total_jobs"] == 1
        assert stats["success_jobs"] == 1

    def test_log_security_event(self, db):
        db.log_security_event(123, "/path/to/file", "Embedded PHP code")
        stats = db.get_total_stats()
        assert stats["total_threats"] == 1


class TestStats:
    def test_empty_stats(self, db):
        stats = db.get_total_stats()
        assert stats["total_users"] == 0
        assert stats["total_photos"] == 0
        assert stats["total_videos"] == 0
        assert stats["total_jobs"] == 0

    def test_increment_processed(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.increment_processed(123, "photo")
        db.increment_processed(123, "photo")
        db.increment_processed(123, "video")
        stats = db.get_total_stats()
        assert stats["total_photos"] == 2
        assert stats["total_videos"] == 1

    def test_processing_time(self, db):
        user = MockUser(123, "testuser", "Test")
        db.upsert_user(user)
        db.add_processing_time(123, 1.5)
        db.add_processing_time(123, 2.5)
        row = db.get_user(123)
        assert row["total_processing_time"] == 4.0
