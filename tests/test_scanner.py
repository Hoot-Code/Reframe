"""Tests for scanner.py — file validation and security scanning."""

import os
import pytest
from scanner import (
    scan_file, _check_image, _check_video,
    _check_malicious, _check_eof, _read_head
)


class TestImageMagicBytes:
    def test_jpeg_valid(self):
        head = b"\xff\xd8\xff" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_png_valid(self):
        head = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_gif87a_valid(self):
        head = b"GIF87a" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_gif89a_valid(self):
        head = b"GIF89a" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_bmp_valid(self):
        head = b"BM" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_webp_valid(self):
        head = b"RIFF\x00\x00\x00\x00WEBP" + b"\x00" * 100
        ok, reason = _check_image(head)
        assert ok is True

    def test_unknown_format_rejected(self):
        head = b"\x00\x00\x00\x00" * 10
        ok, reason = _check_image(head)
        assert ok is False
        assert "does not match" in reason


class TestVideoMagicBytes:
    def test_mp4_valid(self):
        head = b"\x00\x00\x00\x1cftyp" + b"\x00" * 100
        ok, reason = _check_video(head)
        assert ok is True

    def test_avi_valid(self):
        head = b"RIFF\x00\x00\x00\x00AVI " + b"\x00" * 100
        ok, reason = _check_video(head)
        assert ok is True

    def test_mkv_valid(self):
        head = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
        ok, reason = _check_video(head)
        assert ok is True

    def test_flv_valid(self):
        head = b"FLV\x01" + b"\x00" * 100
        ok, reason = _check_video(head)
        assert ok is True

    def test_unknown_format_rejected(self):
        head = b"\x00\x00\x00\x00" * 10
        ok, reason = _check_video(head)
        assert ok is False


class TestMaliciousPatterns:
    def test_php_detected(self):
        head = b"\xff\xd8\xff" + b"\x00" * 50 + b"<?php" + b"\x00" * 50
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "PHP" in threat

    def test_shell_script_detected(self):
        head = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50 + b"#!/bin/bash" + b"\x00" * 50
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "shell" in threat.lower()

    def test_javascript_detected(self):
        head = b"\xff\xd8\xff" + b"\x00" * 50 + b"<script>alert(1)</script>" + b"\x00" * 50
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "JavaScript" in threat

    def test_elf_detected(self):
        head = b"\x7fELF" + b"\x00" * 100
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "ELF" in threat

    def test_pe_detected(self):
        head = b"MZ\x90\x00" + b"\x00" * 100
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "PE" in threat

    def test_zip_detected(self):
        head = b"\xff\xd8\xff" + b"\x00" * 100 + b"PK\x03\x04" + b"\x00" * 50
        safe, threat = _check_malicious(head)
        assert safe is False
        assert "ZIP" in threat

    def test_clean_file_passes(self):
        head = b"\xff\xd8\xff" + b"\x00" * 200
        safe, threat = _check_malicious(head)
        assert safe is True


class TestEOFFlags:
    def test_jpeg_valid_eof(self):
        tail = b"\xff\xd9"
        head = b"\xff\xd8\xff" + b"\x00" * 100
        ok, reason = _check_eof(tail, 10000, "photo", head)
        assert ok is True

    def test_jpeg_invalid_eof(self):
        tail = b"\x00\x00"
        head = b"\xff\xd8\xff" + b"\x00" * 100
        ok, reason = _check_eof(tail, 10000, "photo", head)
        assert ok is False
        assert "JPEG" in reason

    def test_png_not_checked(self):
        tail = b"\x00\x00"
        head = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        ok, reason = _check_eof(tail, 10000, "photo", head)
        assert ok is True

    def test_gif_not_checked(self):
        tail = b"\x3b"
        head = b"GIF89a" + b"\x00" * 100
        ok, reason = _check_eof(tail, 10000, "photo", head)
        assert ok is True


class TestScanFile:
    def test_missing_file(self):
        ok, reason = scan_file("/nonexistent/file.jpg", "photo")
        assert ok is False
        assert "not found" in reason.lower()

    def test_empty_file(self, empty_file):
        ok, reason = scan_file(empty_file, "photo")
        assert ok is False
        assert "empty" in reason.lower()

    def test_valid_jpeg(self, sample_jpeg):
        ok, reason = scan_file(sample_jpeg, "photo")
        assert ok is True

    def test_valid_png(self, sample_png):
        ok, reason = scan_file(sample_png, "photo")
        assert ok is True

    def test_valid_webp(self, sample_webp):
        ok, reason = scan_file(sample_webp, "photo")
        assert ok is True

    def test_valid_mp4(self, sample_mp4):
        ok, reason = scan_file(sample_mp4, "video")
        assert ok is True

    def test_valid_gif(self, sample_gif):
        ok, reason = scan_file(sample_gif, "photo")
        assert ok is True

    def test_valid_bmp(self, sample_bmp):
        ok, reason = scan_file(sample_bmp, "photo")
        assert ok is True

    def test_malicious_php_rejected(self, malicious_php):
        ok, reason = scan_file(malicious_php, "photo")
        assert ok is False
        assert "PHP" in reason

    def test_malicious_script_rejected(self, malicious_script):
        ok, reason = scan_file(malicious_script, "photo")
        assert ok is False

    def test_unknown_media_type(self, sample_jpeg):
        ok, reason = scan_file(sample_jpeg, "audio")
        assert ok is False
        assert "Unknown" in reason

    def test_magic_mismatch_jpeg_as_video(self, sample_jpeg):
        ok, reason = scan_file(sample_jpeg, "video")
        assert ok is False
        assert "does not match" in reason.lower()
