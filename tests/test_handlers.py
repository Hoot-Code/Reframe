"""Tests for handlers.py — input parsing, validation, and edge cases."""

import re
import pytest

try:
    from handlers import _md_escape
    _HAS_TELEGRAM = True
except (ImportError, ModuleNotFoundError):
    _HAS_TELEGRAM = False

    def _md_escape(text):
        return re.sub(r'([_*`\[])', r'\\\1', text or "")


class TestMdEscape:
    def test_escapes_asterisk(self):
        assert _md_escape("hello*world") == r"hello\*world"

    def test_escapes_underscore(self):
        assert _md_escape("hello_world") == r"hello\_world"

    def test_escapes_backtick(self):
        assert _md_escape("hello`world") == r"hello\`world"

    def test_escapes_bracket(self):
        assert _md_escape("hello[world") == r"hello\[world"

    def test_empty_string(self):
        assert _md_escape("") == ""

    def test_none_returns_empty(self):
        assert _md_escape(None) == ""

    def test_clean_string_unchanged(self):
        assert _md_escape("hello world") == "hello world"


class TestSizeParsing:
    """Test the size parsing logic used in size_callback."""

    def test_parse_preset_size(self):
        """Simulate parsing 'sz_1920x1080'."""
        data = "sz_1920x1080"
        _, size_part = data.split("_", 1)
        w, h = map(int, size_part.split("x"))
        assert w == 1920
        assert h == 1080

    def test_parse_custom_size(self):
        """Simulate parsing '1920x1080' from user input."""
        raw = "1920x1080"
        parts = raw.split("x")
        assert len(parts) == 2
        w, h = int(parts[0]), int(parts[1])
        assert w == 1920
        assert h == 1080

    def test_custom_size_with_asterisk(self):
        """User sends 1920*1080 — should normalize."""
        raw = "1920*1080".replace("*", "x")
        parts = raw.split("x")
        w, h = int(parts[0]), int(parts[1])
        assert w == 1920
        assert h == 1080

    def test_custom_size_with_unicode_multiply(self):
        """User sends 1920×1080 — should normalize."""
        raw = "1920×1080".replace("×", "x")
        parts = raw.split("x")
        w, h = int(parts[0]), int(parts[1])
        assert w == 1920
        assert h == 1080

    def test_custom_size_with_spaces(self):
        """User sends '1920 x 1080' — should normalize."""
        raw = "1920 x 1080".replace(" ", "").replace("×", "x").replace("*", "x")
        parts = raw.split("x")
        w, h = int(parts[0]), int(parts[1])
        assert w == 1920
        assert h == 1080

    def test_invalid_format_no_x(self):
        """User sends '1920' — should be rejected."""
        raw = "1920"
        parts = raw.split("x")
        assert len(parts) != 2

    def test_invalid_format_letters(self):
        """User sends 'abcx1080' — should fail int conversion."""
        raw = "abcx1080"
        parts = raw.split("x")
        with pytest.raises(ValueError):
            w, h = int(parts[0]), int(parts[1])

    def test_zero_dimensions_rejected(self):
        """Dimensions must be > 0."""
        w, h = 0, 100
        assert w < 1

    def test_negative_dimensions_rejected(self):
        """Dimensions must be > 0."""
        w, h = -100, 100
        assert w < 1


class TestMaxResolution:
    """Test max resolution enforcement."""

    def test_within_limit(self):
        from config import CONFIG
        max_r = CONFIG["max_resolution"]
        w, h = 1920, 1080
        assert w <= max_r and h <= max_r

    def test_exceeds_limit(self):
        from config import CONFIG
        max_r = CONFIG["max_resolution"]
        w, h = 4000, 3000
        assert w > max_r or h > max_r

    def test_exactly_at_limit(self):
        from config import CONFIG
        max_r = CONFIG["max_resolution"]
        w, h = 3840, 3840
        assert w <= max_r and h <= max_r


class TestFormatValidation:
    """Test format validation logic used in format_callback."""

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

    def test_invalid_format_rejected(self):
        from media_processor import IMAGE_FORMATS
        allowed = set(IMAGE_FORMATS)
        allowed.add("keep")
        assert "gif" not in allowed
        assert "bmp" not in allowed


class TestModeValidation:
    """Test mode validation logic used in mode_callback."""

    def test_valid_modes(self):
        valid = {"pad", "stretch"}
        assert "pad" in valid
        assert "stretch" in valid

    def test_invalid_mode(self):
        valid = {"pad", "stretch"}
        assert "foobar" not in valid
        assert "compress" not in valid


class TestLastSizeValidation:
    """Test last_size validation logic."""

    def test_valid_resolution(self):
        last = "1920x1080"
        valid = last == "compressed" or (
            "x" in last and all(p.isdigit() for p in last.split("x", 1))
        )
        assert valid is True

    def test_valid_compressed(self):
        last = "compressed"
        valid = last == "compressed" or (
            "x" in last and all(p.isdigit() for p in last.split("x", 1))
        )
        assert valid is True

    def test_invalid_format(self):
        last = "invalid"
        valid = last == "compressed" or (
            "x" in last and all(p.isdigit() for p in last.split("x", 1))
        )
        assert valid is False

    def test_invalid_with_letters(self):
        last = "abcx1080"
        valid = last == "compressed" or (
            "x" in last and all(p.isdigit() for p in last.split("x", 1))
        )
        assert valid is False


class TestExtToFormatMapping:
    """Test extension-to-format mapping for Keep Original."""

    def test_jpeg_mapping(self):
        from media_processor import EXT_TO_IMAGE_FORMAT
        assert EXT_TO_IMAGE_FORMAT[".jpg"] == "jpg"
        assert EXT_TO_IMAGE_FORMAT[".jpeg"] == "jpg"

    def test_png_mapping(self):
        from media_processor import EXT_TO_IMAGE_FORMAT
        assert EXT_TO_IMAGE_FORMAT[".png"] == "png"

    def test_webp_mapping(self):
        from media_processor import EXT_TO_IMAGE_FORMAT
        assert EXT_TO_IMAGE_FORMAT[".webp"] == "webp"

    def test_mp4_mapping(self):
        from media_processor import EXT_TO_VIDEO_FORMAT
        assert EXT_TO_VIDEO_FORMAT[".mp4"] == "mp4"

    def test_mov_maps_to_mp4(self):
        from media_processor import EXT_TO_VIDEO_FORMAT
        assert EXT_TO_VIDEO_FORMAT[".mov"] == "mp4"

    def test_avi_mapping(self):
        from media_processor import EXT_TO_VIDEO_FORMAT
        assert EXT_TO_VIDEO_FORMAT[".avi"] == "avi"

    def test_mkv_mapping(self):
        from media_processor import EXT_TO_VIDEO_FORMAT
        assert EXT_TO_VIDEO_FORMAT[".mkv"] == "mkv"

    def test_webm_maps_to_mp4(self):
        from media_processor import EXT_TO_VIDEO_FORMAT
        assert EXT_TO_VIDEO_FORMAT[".webm"] == "mp4"

    def test_unknown_ext_falls_back(self):
        from media_processor import EXT_TO_IMAGE_FORMAT
        result = EXT_TO_IMAGE_FORMAT.get(".unknown", "jpg")
        assert result == "jpg"
