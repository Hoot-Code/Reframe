"""
database.py —
Dual-backend database manager: SQLite (default) or PostgreSQL.
Thread-safe with connection pooling for production use.
"""

import os
import atexit
import threading
import logging
from datetime import datetime, timedelta

from config import DB_BACKEND, DB_FILE, DB_URL

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Unified database interface — works with both SQLite and PostgreSQL."""

    def __init__(self, backend: str = None, db_url: str = None, db_path: str = None):
        self.backend = backend or DB_BACKEND
        self._lock = threading.Lock()

        if self.backend == "postgresql":
            self._init_postgres(db_url or DB_URL)
        else:
            self._init_sqlite(db_path or DB_FILE)

        self._init_tables()
        atexit.register(self._close)

    # ── PostgreSQL ─────────────────────────────────────────────────────────────
    def _init_postgres(self, url: str):
        try:
            import psycopg2
            import psycopg2.pool
            self._pg_pool = psycopg2.pool.ThreadedConnectionPool(2, 20, url)
            self._pg_dsn = url
            logger.info(f"PostgreSQL connected: {url.split('@')[-1] if '@' in url else url}")
        except ImportError:
            logger.warning("psycopg2 not installed — falling back to SQLite")
            self.backend = "sqlite"
            self._init_sqlite(DB_FILE)
        except Exception as exc:
            logger.error(f"PostgreSQL connection failed: {exc} — falling back to SQLite")
            self.backend = "sqlite"
            self._init_sqlite(DB_FILE)

    def _pg_conn(self):
        return self._pg_pool.getconn()

    def _pg_put(self, conn):
        self._pg_pool.putconn(conn)

    # ── SQLite ─────────────────────────────────────────────────────────────────
    def _init_sqlite(self, path: str):
        import sqlite3
        self.db_path = path
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        logger.info(f"SQLite connected: {path}")

    # ── Schema ─────────────────────────────────────────────────────────────────
    def _init_tables(self):
        if self.backend == "postgresql":
            self._init_pg_tables()
        else:
            self._init_sqlite_tables()

    def _init_pg_tables(self):
        conn = self._pg_conn()
        try:
            c = conn.cursor()
            c.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id               BIGINT PRIMARY KEY,
                    username              TEXT,
                    first_name            TEXT,
                    joined_date           TEXT,
                    photos_processed      INTEGER DEFAULT 0,
                    videos_processed      INTEGER DEFAULT 0,
                    last_size             TEXT,
                    is_banned             INTEGER DEFAULT 0,
                    total_processing_time REAL DEFAULT 0,
                    language              TEXT DEFAULT 'en'
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS process_logs (
                    id              SERIAL PRIMARY KEY,
                    user_id         BIGINT,
                    media_type      TEXT,
                    dimensions      TEXT,
                    mode            TEXT,
                    output_format   TEXT,
                    status          TEXT,
                    processing_time REAL,
                    error_details   TEXT,
                    timestamp       TEXT
                )
            """)
            c.execute("""
                CREATE TABLE IF NOT EXISTS security_logs (
                    id        SERIAL PRIMARY KEY,
                    user_id   BIGINT,
                    file_path TEXT,
                    threat    TEXT,
                    timestamp TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_process_logs_ts ON process_logs(timestamp)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_security_logs_ts ON security_logs(timestamp)")
            conn.commit()
        finally:
            self._pg_put(conn)

    def _init_sqlite_tables(self):
        with self._lock:
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
            for col, definition in [
                ("language", "TEXT DEFAULT 'en'"),
                ("total_processing_time", "REAL DEFAULT 0"),
            ]:
                try:
                    c.execute(f"ALTER TABLE users ADD COLUMN {col} {definition}")
                except Exception:
                    pass
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
        try:
            if self.backend == "postgresql":
                self._pg_pool.closeall()
            else:
                self.conn.close()
        except Exception:
            pass

    # ── Unified execute ────────────────────────────────────────────────────────
    def execute(self, query: str, params=(), *,
                commit=False, fetch_one=False, fetch_all=False):
        if self.backend == "postgresql":
            return self._execute_pg(query, params, commit=commit,
                                    fetch_one=fetch_one, fetch_all=fetch_all)
        return self._execute_sqlite(query, params, commit=commit,
                                    fetch_one=fetch_one, fetch_all=fetch_all)

    def _execute_pg(self, query, params, *, commit, fetch_one, fetch_all):
        conn = self._pg_conn()
        try:
            c = conn.cursor()
            c.execute(query, params)
            result = None
            if fetch_one:
                result = c.fetchone()
                if result:
                    result = _PgRow(c.description, result)
            elif fetch_all:
                result = [_PgRow(c.description, r) for r in c.fetchall()]
            if commit:
                conn.commit()
            return result
        except Exception as e:
            conn.rollback()
            logger.error(f"PG error: {e} | query={query!r}")
            return None
        finally:
            self._pg_put(conn)

    def _execute_sqlite(self, query, params, *, commit, fetch_one, fetch_all):
        with self._lock:
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
            except Exception as e:
                logger.error(f"SQLite error: {e} | query={query!r}")
                return None

    # ── Users ──────────────────────────────────────────────────────────────────
    def upsert_user(self, user) -> None:
        if self.backend == "postgresql":
            self.execute(
                """
                INSERT INTO users (user_id, username, first_name, joined_date)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = EXCLUDED.username,
                    first_name = EXCLUDED.first_name
                """,
                (user.id, user.username, user.first_name, str(datetime.now())),
                commit=True,
            )
        else:
            self.execute(
                """
                INSERT INTO users (user_id, username, first_name, joined_date)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name
                """,
                (user.id, user.username, user.first_name, str(datetime.now())),
                commit=True,
            )

    def get_user(self, user_id: int):
        ph = "%s" if self.backend == "postgresql" else "?"
        return self.execute(f"SELECT * FROM users WHERE user_id = {ph}", (user_id,), fetch_one=True)

    def get_all_user_ids(self) -> list[int]:
        rows = self.execute("SELECT user_id FROM users", fetch_all=True)
        return [r["user_id"] for r in rows] if rows else []

    def set_ban_status(self, user_id: int, banned: bool) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(
            f"UPDATE users SET is_banned = {ph} WHERE user_id = {ph}",
            (1 if banned else 0, user_id), commit=True,
        )

    def set_user_language(self, user_id: int, lang: str) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(
            f"UPDATE users SET language = {ph} WHERE user_id = {ph}",
            (lang, user_id), commit=True,
        )

    def get_user_language(self, user_id: int) -> str:
        ph = "%s" if self.backend == "postgresql" else "?"
        row = self.execute(f"SELECT language FROM users WHERE user_id = {ph}", (user_id,), fetch_one=True)
        return (row["language"] or "en") if row else "en"

    def increment_processed(self, user_id: int, media_type: str) -> None:
        col = "photos_processed" if media_type == "photo" else "videos_processed"
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(f"UPDATE users SET {col} = {col} + 1 WHERE user_id = {ph}", (user_id,), commit=True)

    def update_last_size(self, user_id: int, size_str: str) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(f"UPDATE users SET last_size = {ph} WHERE user_id = {ph}", (size_str, user_id), commit=True)

    def add_processing_time(self, user_id: int, seconds: float) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(
            f"UPDATE users SET total_processing_time = total_processing_time + {ph} WHERE user_id = {ph}",
            (seconds, user_id), commit=True,
        )

    # ── Settings ───────────────────────────────────────────────────────────────
    def set_setting(self, key: str, value) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        if self.backend == "postgresql":
            self.execute(
                f"INSERT INTO settings (key, value) VALUES ({ph}, {ph}) ON CONFLICT(key) DO UPDATE SET value = EXCLUDED.value",
                (key, str(value)), commit=True,
            )
        else:
            self.execute(
                f"INSERT OR REPLACE INTO settings (key, value) VALUES ({ph}, {ph})",
                (key, str(value)), commit=True,
            )

    def get_setting(self, key: str):
        ph = "%s" if self.backend == "postgresql" else "?"
        row = self.execute(f"SELECT value FROM settings WHERE key = {ph}", (key,), fetch_one=True)
        return row["value"] if row else None

    # ── Logs ───────────────────────────────────────────────────────────────────
    def log_process(self, user_id: int, media_type: str, dimensions: str,
                    mode: str, output_format: str, status: str,
                    processing_time: float, error_details: str = None) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(
            f"""INSERT INTO process_logs
                (user_id, media_type, dimensions, mode, output_format,
                 status, processing_time, error_details, timestamp)
            VALUES ({ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph}, {ph})""",
            (user_id, media_type, dimensions, mode, output_format,
             status, processing_time, error_details, str(datetime.now())),
            commit=True,
        )

    def log_security_event(self, user_id: int, file_path: str, threat: str) -> None:
        ph = "%s" if self.backend == "postgresql" else "?"
        self.execute(
            f"INSERT INTO security_logs (user_id, file_path, threat, timestamp) VALUES ({ph}, {ph}, {ph}, {ph})",
            (user_id, file_path, threat, str(datetime.now())), commit=True,
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

    # ── Log rotation ───────────────────────────────────────────────────────────
    def rotate_logs(self, days_to_keep: int = 30) -> int:
        cutoff = (datetime.now() - timedelta(days=days_to_keep)).isoformat()
        ph = "%s" if self.backend == "postgresql" else "?"
        if self.backend == "postgresql":
            conn = self._pg_conn()
            try:
                c = conn.cursor()
                c.execute(f"DELETE FROM process_logs WHERE timestamp < {ph}", (cutoff,))
                p = c.rowcount
                c.execute(f"DELETE FROM security_logs WHERE timestamp < {ph}", (cutoff,))
                s = c.rowcount
                conn.commit()
            finally:
                self._pg_put(conn)
        else:
            with self._lock:
                c = self.conn.cursor()
                c.execute(f"DELETE FROM process_logs WHERE timestamp < {ph}", (cutoff,))
                p = c.rowcount
                c.execute(f"DELETE FROM security_logs WHERE timestamp < {ph}", (cutoff,))
                s = c.rowcount
                self.conn.commit()
        total = p + s
        if total:
            logger.info(f"Log rotation: deleted {p} process + {s} security entries older than {days_to_keep} days")
        return total


class _PgRow:
    """Dict-like wrapper for PostgreSQL rows."""
    def __init__(self, description, row):
        self._keys = [d[0] for d in description]
        self._values = row
    def __getitem__(self, key):
        return self._values[self._keys.index(key)]
    def __contains__(self, key):
        return key in self._keys
    def get(self, key, default=None):
        try:
            return self[key]
        except (IndexError, ValueError):
            return default


# ── Singleton ──────────────────────────────────────────────────────────────────
db = DatabaseManager()
