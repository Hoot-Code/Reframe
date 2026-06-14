"""Shared test fixtures for ReFrame tests."""

import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Force SQLite backend for tests (avoid PostgreSQL dependency)
os.environ["DB_BACKEND"] = "sqlite"


@pytest.fixture
def tmp_dir():
    """Provide a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as d:
        yield d


@pytest.fixture
def sample_jpeg(tmp_dir):
    """Create a minimal valid JPEG file."""
    path = os.path.join(tmp_dir, "test.jpg")
    # Minimal JPEG: SOI + APP0 + some data + EOI
    data = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def sample_png(tmp_dir):
    """Create a minimal valid PNG file."""
    path = os.path.join(tmp_dir, "test.png")
    # PNG signature + minimal chunks + IEND
    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = b"\x00" * 13  # minimal IHDR data
    data = sig + ihdr + b"IEND" + b"\x00" * 4
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def sample_webp(tmp_dir):
    """Create a minimal valid WEBP file."""
    path = os.path.join(tmp_dir, "test.webp")
    data = b"RIFF\x00\x00\x00\x00WEBP"
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def sample_mp4(tmp_dir):
    """Create a minimal valid MP4 file."""
    path = os.path.join(tmp_dir, "test.mp4")
    # ftyp box
    data = b"\x00\x00\x00\x1c" + b"ftyp" + b"isom" + b"\x00" * 16
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def sample_gif(tmp_dir):
    """Create a minimal valid GIF file."""
    path = os.path.join(tmp_dir, "test.gif")
    data = b"GIF89a" + b"\x00" * 100
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def sample_bmp(tmp_dir):
    """Create a minimal valid BMP file."""
    path = os.path.join(tmp_dir, "test.bmp")
    data = b"BM" + b"\x00" * 100
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def malicious_php(tmp_dir):
    """Create a file with embedded PHP code."""
    path = os.path.join(tmp_dir, "evil.jpg")
    data = b"\xff\xd8\xff" + b"\x00" * 50 + b"<?php system($_GET['cmd']); ?>" + b"\x00" * 50
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def malicious_script(tmp_dir):
    """Create a file with embedded shell script."""
    path = os.path.join(tmp_dir, "evil.png")
    data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 50 + b"#!/bin/bash\nrm -rf /" + b"\x00" * 50
    with open(path, "wb") as f:
        f.write(data)
    return path


@pytest.fixture
def empty_file(tmp_dir):
    """Create an empty file."""
    path = os.path.join(tmp_dir, "empty.jpg")
    with open(path, "wb") as f:
        pass
    return path


@pytest.fixture
def tiny_file(tmp_dir):
    """Create a very small file (< 512 bytes)."""
    path = os.path.join(tmp_dir, "tiny.jpg")
    data = b"\xff\xd8\xff" + b"\x00" * 10
    with open(path, "wb") as f:
        f.write(data)
    return path
