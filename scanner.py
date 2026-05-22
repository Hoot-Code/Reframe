"""
scanner.py — Hoot-code Bot
Security scanner: validates file magic bytes against claimed type and
searches for embedded malicious patterns (scripts, executables, polyglots).
Any file that fails is deleted immediately and the event is logged to DB.
"""

import os
import logging

logger = logging.getLogger(__name__)

# ── Magic-byte signatures ──────────────────────────────────────────────────────
# Each entry: signature_bytes -> (offset, human_name)
IMAGE_MAGIC: list[tuple[bytes, int, str]] = [
    (b"\xff\xd8\xff",          0, "JPEG"),
    (b"\x89PNG\r\n\x1a\n",    0, "PNG"),
    (b"GIF87a",                0, "GIF"),
    (b"GIF89a",                0, "GIF"),
    (b"BM",                    0, "BMP"),
    # WEBP: "RIFF" at 0, "WEBP" at 8
]

VIDEO_MAGIC: list[tuple[bytes, int, str]] = [
    # MKV / WEBM
    (b"\x1a\x45\xdf\xa3",     0, "MKV/WEBM"),
    # FLV
    (b"FLV\x01",              0, "FLV"),
]

# Patterns that are ALWAYS suspicious regardless of claimed type
MALICIOUS_PATTERNS: list[tuple[bytes, str]] = [
    (b"<?php",          "Embedded PHP code"),
    (b"<%@",            "Embedded server-side script"),
    (b"<script",        "Embedded JavaScript"),
    (b"#!/bin/",        "Embedded shell script"),
    (b"#!/usr/bin/",    "Embedded shell script"),
    (b"\x7fELF",        "ELF executable"),
    (b"MZ\x90\x00",    "Windows PE executable"),   # more specific than bare MZ
]

# Read this many bytes for the scan (8 KB is enough for headers)
SCAN_BYTES = 8192


# ── Internal helpers ───────────────────────────────────────────────────────────
def _read_head(path: str) -> bytes:
    size = os.path.getsize(path)
    with open(path, "rb") as fh:
        return fh.read(min(SCAN_BYTES, size))


def _check_image(head: bytes) -> tuple[bool, str]:
    """Return (ok, reason). WEBP needs an extra check."""
    for sig, offset, name in IMAGE_MAGIC:
        if head[offset:offset + len(sig)] == sig:
            return True, ""

    # WEBP: b"RIFF" at 0 AND b"WEBP" at 8
    if head[:4] == b"RIFF" and len(head) >= 12 and head[8:12] == b"WEBP":
        return True, ""

    return False, "File header does not match any known image format"


def _check_video(head: bytes) -> tuple[bool, str]:
    """Return (ok, reason)."""
    # MP4 / MOV: 4-byte length + b"ftyp" at offset 4
    if len(head) >= 8 and head[4:8] == b"ftyp":
        return True, ""

    # AVI: b"RIFF" at 0, b"AVI " at 8
    if head[:4] == b"RIFF" and len(head) >= 12 and head[8:12] == b"AVI ":
        return True, ""

    for sig, offset, name in VIDEO_MAGIC:
        if head[offset:offset + len(sig)] == sig:
            return True, ""

    return False, "File header does not match any known video format"


def _check_malicious(head: bytes) -> tuple[bool, str]:
    """Return (safe, threat_description)."""
    lower = head.lower()
    for pattern, label in MALICIOUS_PATTERNS:
        if pattern.lower() in lower:
            return False, label

    # Embedded ZIP in the middle of the data (possible polyglot / zip-bomb)
    # Skip first 64 bytes to avoid false positives on formats that legitimately
    # begin with a local file header (e.g. ODT, DOCX are ZIP-based, but those
    # should never be sent here as images/videos).
    if b"PK\x03\x04" in head[64:]:
        return False, "Embedded ZIP archive (possible polyglot file)"

    return True, ""


# ── Public API ─────────────────────────────────────────────────────────────────
def scan_file(file_path: str, media_type: str) -> tuple[bool, str]:
    """
    Full security scan.

    Parameters
    ----------
    file_path  : absolute path to the downloaded file
    media_type : "photo" | "video"

    Returns
    -------
    (True, "")              — file is safe
    (False, reason_string)  — file is dangerous; caller must delete it
    """
    try:
        if not os.path.exists(file_path):
            return False, "File not found after download"

        if os.path.getsize(file_path) == 0:
            return False, "File is empty"

        head = _read_head(file_path)

        # 1. Magic-byte validation
        if media_type == "photo":
            ok, reason = _check_image(head)
        elif media_type == "video":
            ok, reason = _check_video(head)
        else:
            ok, reason = False, f"Unknown media_type: {media_type!r}"

        if not ok:
            logger.warning(f"[SCAN] Magic mismatch — {file_path}: {reason}")
            return False, reason

        # 2. Malicious-pattern scan
        safe, threat = _check_malicious(head)
        if not safe:
            logger.warning(f"[SCAN] Threat detected — {file_path}: {threat}")
            return False, threat

        logger.info(f"[SCAN] OK — {file_path}")
        return True, ""

    except OSError as exc:
        msg = f"Cannot read file for scanning: {exc}"
        logger.error(f"[SCAN] {msg}")
        return False, msg
