"""
locustfile.py —
Load testing configuration for ReFrame bot.
Tests scanner, database, and media processor under load.

Usage:
    locust -f locustfile.py --host=http://localhost:9090
"""

import os
import tempfile
from locust import task, between
from locust.contrib.fasthttp import FastHttpUser


class ScannerLoadTest(FastHttpUser):
    """Load test the scanner endpoint."""
    wait_time = between(0.1, 0.5)

    def on_start(self):
        self._create_test_files()

    def _create_test_files(self):
        self.test_files = {}
        with tempfile.TemporaryDirectory() as tmpdir:
            # Valid JPEG
            path = os.path.join(tmpdir, "test.jpg")
            data = b"\xff\xd8\xff\xe0" + b"\x00" * 100 + b"\xff\xd9"
            with open(path, "wb") as f:
                f.write(data)
            self.test_files["jpeg"] = path

            # Valid PNG
            path = os.path.join(tmpdir, "test.png")
            data = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100 + b"IEND" + b"\x00" * 4
            with open(path, "wb") as f:
                f.write(data)
            self.test_files["png"] = path

    @task(10)
    def scan_valid_jpeg(self):
        from scanner import scan_file
        scan_file(self.test_files["jpeg"], "photo")

    @task(10)
    def scan_valid_png(self):
        from scanner import scan_file
        scan_file(self.test_files["png"], "photo")

    @task(2)
    def scan_missing_file(self):
        from scanner import scan_file
        scan_file("/nonexistent/file.jpg", "photo")


class DatabaseLoadTest(FastHttpUser):
    """Load test database operations."""
    wait_time = between(0.01, 0.1)

    def on_start(self):
        from database import DatabaseManager
        with tempfile.TemporaryDirectory() as tmpdir:
            self.db = DatabaseManager(os.path.join(tmpdir, "load_test.db"))

    @task(5)
    def upsert_user(self):
        class MockUser:
            id = 10000 + int(os.urandom(2).hex(), 16) % 90000
            username = "loadtest"
            first_name = "Load"
        self.db.upsert_user(MockUser())

    @task(10)
    def get_user(self):
        self.db.get_user(10001)

    @task(3)
    def update_last_size(self):
        self.db.update_last_size(10001, "1920x1080")

    @task(2)
    def log_process(self):
        self.db.log_process(10001, "photo", "1920x1080", "pad", "jpg", "success", 1.0)
