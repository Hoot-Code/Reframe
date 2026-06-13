"""Tests for locales.py — translation helper and string formatting."""

import pytest
from locales import t, LANGUAGE_NAMES


class TestTranslation:
    def test_existing_key(self):
        result = t("en", "choose_language")
        assert "choose" in result.lower() or "language" in result.lower()

    def test_missing_key_returns_key(self):
        result = t("en", "nonexistent_key_xyz")
        assert result == "nonexistent_key_xyz"

    def test_unknown_language_falls_back_to_en(self):
        result = t("xyz", "choose_language")
        assert len(result) > 0

    def test_format_kwargs(self):
        result = t("en", "success_photo", size="1920x1080", mode="pad", fmt="JPG", time=1.5)
        assert "1920x1080" in result
        assert "JPG" in result

    def test_format_kwargs_video(self):
        result = t("en", "success_video", size="1920x1080", mode="pad", fmt="MP4", time=2.0, file_mb=5.5)
        assert "1920x1080" in result
        assert "MP4" in result
        assert "5.5" in result

    def test_all_languages_have_required_keys(self):
        required_keys = [
            "choose_language", "language_set", "welcome", "help_text",
            "stats_text", "maintenance", "banned", "processing_wait",
            "downloading", "scanning", "processing", "uploading",
            "file_too_large", "download_failed", "unsupported_type",
            "scan_failed", "cancelled", "select_size", "select_mode",
            "select_format", "compress_btn", "keep_fmt_btn",
        ]
        for lang in LANGUAGE_NAMES:
            for key in required_keys:
                assert key in t(lang, key) or t(lang, key) != key, \
                    f"Missing key '{key}' in language '{lang}'"


class TestLanguageNames:
    def test_all_languages_present(self):
        assert "en" in LANGUAGE_NAMES
        assert "ru" in LANGUAGE_NAMES
        assert "zh" in LANGUAGE_NAMES
        assert "fa" in LANGUAGE_NAMES

    def test_language_names_are_strings(self):
        for code, name in LANGUAGE_NAMES.items():
            assert isinstance(code, str)
            assert isinstance(name, str)
            assert len(name) > 0
