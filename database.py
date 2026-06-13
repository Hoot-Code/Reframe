"""
database.py 
Thread-safe SQLite manager with user stats, settings, process logs,
security event logs, and per-user language preference.
"""

import sqlite3
import atexit
import threading
import logging
from datetime import datetime

from config import DB_FILE

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str = DB_FILE):
        self.db_path = db_path
        self.lock    = threading.Lock()
        self.conn    = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_tables()
        atexit.register(self._close)

    # ── Schema ─────────────────────────────────────────────────────────────────
    def _init_tables(self):
        with self.lock:
            c = self.conn.cursor()

            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id               INTEGER PRIMARY KEY,
                    username              TEXT,
                    first_name            TEXT,
                    joined_date           TEXT,
                    photos_processed      INTEGER DEFAULT 0,
                    videos_processed      INTEGER DEFAULT 0,
                    last_size             TEXT,
                    is_banned             INTEGER DEFAULT 0,
                    total_processing_time REAL    DEFAULT 0,
                    language              TEXT    DEFAULT 'en'
                )
            """)

            # Live-migration: add columns that may not exist in older DBs
            for col, definition in [
                ("language", "TEXT DEFAULT 'en'"),
                ("total_processing_time", "REAL DEFAULT 0"),
            ]:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                except sqlite3.OperationalError:
                    pass   # column already present

            c.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS process_logs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER,
                    media_type      TEXT,
                    dimensions      TEXT,
                    mode            TEXT,
                    output_format   TEXT,
                    status          TEXT,
                    processing_time REAL,
                    error_details   TEXT,
                    timestamp       TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )
            """)

            c.execute("""
                CREATE TABLE IF NOT EXISTS security_logs (
                    id        INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id   INTEGER,
                    file_path TEXT,
                    threat    TEXT,
                    timestamp TEXT
                )
            """)

            self.conn.commit()

    def _close(self):
        """Close DB connection cleanly on shutdown."""
        try:
            self.conn.close()
        except Exception:
            pass

    # ── Low-level execute ──────────────────────────────────────────────────────
    def execute(self, query: str, params=(), *,
                commit=False, fetch_one=False, fetch_all=False):
        with self.lock:
            try:
                c = self.conn.cursor()
                c.execute(query, params)
                result = None
                if fetch_one:
                    result = c.fetchone()
                elif fetch_all:
                    result = c.fetchall()
                if commit:
                    self.conn.commit()
                return result
            except sqlite3.Error as e:
                logger.error(f"DB error: {e} | query={query!r} params={params}")
                return None

    # ── Users ──────────────────────────────────────────────────────────────────
    def upsert_user(self, user) -> None:
        self.execute(
            """
            INSERT INTO users (user_id, username, first_name, joined_date)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username   = excluded.username,
                first_name = excluded.first_name
            """,
            (user.id, user.username, user.first_name, str(datetime.now())),
            commit=True,
        )

    def get_user(self, user_id: int):
        return self.execute(
            "SELECT * FROM users WHERE user_id = ?", (user_id,), fetch_one=True
        )

    def get_all_user_ids(self) -> list[int]:
        rows = self.execute("SELECT user_id FROM users", fetch_all=True)
        return [r["user_id"] for r in rows] if rows else []

    def set_ban_status(self, user_id: int, banned: bool) -> None:
        self.execute(
            "UPDATE users SET is_banned = ? WHERE user_id = ?",
            (1 if banned else 0, user_id),
            commit=True,
        )

    def set_user_language(self, user_id: int, lang: str) -> None:
        self.execute(
            "UPDATE users SET language = ? WHERE user_id = ?",
            (lang, user_id),
            commit=True,
        )

    def get_user_language(self, user_id: int) -> str:
        row = self.execute(
            "SELECT language FROM users WHERE user_id = ?", (user_id,), fetch_one=True
        )
        return (row["language"] or "en") if row else "en"

    def increment_processed(self, user_id: int, media_type: str) -> None:
        col = "photos_processed" if media_type == "photo" else "videos_processed"
        self.execute(
            f"UPDATE users SET {col} = {col} + 1 WHERE user_id = ?",
            (user_id,),
            commit=True,
        )

    def update_last_size(self, user_id: int, size_str: str) -> None:
        self.execute(
            "UPDATE users SET last_size = ? WHERE user_id = ?",
            (size_str, user_id),
            commit=True,
        )

    def add_processing_time(self, user_id: int, seconds: float) -> None:
        self.execute(
            "UPDATE users SET total_processing_time = total_processing_time + ? WHERE user_id = ?",
            (seconds, user_id),
            commit=True,
        )

    # ── Settings ───────────────────────────────────────────────────────────────
    def set_setting(self, key: str, value) -> None:
        self.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, str(value)),
            commit=True,
        )

    def get_setting(self, key: str):
        row = self.execute(
            "SELECT value FROM settings WHERE key = ?", (key,), fetch_one=True
        )
        return row["value"] if row else None

    # ── Logs ───────────────────────────────────────────────────────────────────
    def log_process(self, user_id: int, media_type: str, dimensions: str,
                    mode: str, output_format: str, status: str,
                    processing_time: float, error_details: str = None) -> None:
        self.execute(
            """
            INSERT INTO process_logs
                (user_id, media_type, dimensions, mode, output_format,
                 status, processing_time, error_details, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, media_type, dimensions, mode, output_format,
             status, processing_time, error_details, str(datetime.now())),
            commit=True,
        )

    def log_security_event(self, user_id: int, file_path: str, threat: str) -> None:
        self.execute(
            "INSERT INTO security_logs (user_id, file_path, threat, timestamp) VALUES (?, ?, ?, ?)",
            (user_id, file_path, threat, str(datetime.now())),
            commit=True,
        )

    # ── Aggregate stats ────────────────────────────────────────────────────────
    def get_total_stats(self) -> dict:
        row = self.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM users) AS total_users,
                (SELECT COALESCE(SUM(photos_processed),0) FROM users) AS total_photos,
                (SELECT COALESCE(SUM(videos_processed),0) FROM users) AS total_videos,
                (SELECT COUNT(*) FROM users WHERE is_banned=1) AS total_banned,
                (SELECT COUNT(*) FROM security_logs) AS total_threats,
                (SELECT COUNT(*) FROM process_logs) AS total_jobs,
                (SELECT COUNT(*) FROM process_logs WHERE status='success') AS success_jobs
            """,
            fetch_one=True,
        )
        if not row:
            return {k: 0 for k in ("total_users","total_photos","total_videos",
                                    "total_banned","total_threats","total_jobs","success_jobs")}
        return {k: row[k] for k in ("total_users","total_photos","total_videos",
                                     "total_banned","total_threats","total_jobs","success_jobs")}


# ── Singleton ──────────────────────────────────────────────────────────────────
db = DatabaseManager()
