"""
SQLite Database Manager for FaceSoter with WAL mode, transactions, and migration runner.
"""

from __future__ import annotations
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator
from facesoter.core.database.schema import SCHEMA_VERSION, MIGRATIONS
from facesoter.core.logging.logger import get_logger

logger = get_logger("database")


class DatabaseManager:
    """Thread-safe SQLite database manager."""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self.initialize()

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=60.0,
                check_same_thread=False,
            )
            conn.row_factory = sqlite3.Row
            # Enable foreign keys & WAL mode for performance and reliability
            conn.execute("PRAGMA foreign_keys = ON;")
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA synchronous = NORMAL;")
            conn.execute("PRAGMA busy_timeout = 30000;")
            self._local.conn = conn
        return self._local.conn

    def close(self) -> None:
        """Close thread-local connection."""
        if hasattr(self._local, "conn") and self._local.conn is not None:
            try:
                self._local.conn.close()
            except Exception:
                pass
            self._local.conn = None

    @contextmanager
    def transaction(self) -> Generator[sqlite3.Cursor, None, None]:
        """Transactional context manager committing on success or rolling back on error."""
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            yield cursor
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction failed, rolled back: {e}")
            raise
        finally:
            cursor.close()

    def initialize(self) -> None:
        """Run schema migrations up to current SCHEMA_VERSION."""
        with self._lock:
            conn = self.get_connection()
            # Ensure migrations table exists
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
            """)
            conn.commit()

            # Check applied version
            cur = conn.cursor()
            cur.execute("SELECT MAX(version) FROM schema_migrations")
            row = cur.fetchone()
            current_ver = row[0] if row and row[0] is not None else 0

            for ver in range(current_ver + 1, SCHEMA_VERSION + 1):
                if ver in MIGRATIONS:
                    logger.info(f"Applying database migration version {ver}...")
                    conn.executescript(MIGRATIONS[ver])
                    now_str = datetime.now(timezone.utc).isoformat()
                    conn.execute(
                        "INSERT INTO schema_migrations (version, applied_at) VALUES (?, ?)",
                        (ver, now_str),
                    )
                    conn.commit()
                    logger.info(f"Migration version {ver} applied successfully.")
