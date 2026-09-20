"""
Repository for application settings and registered AI models.
"""

from __future__ import annotations
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from facesoter.core.database.db_manager import DatabaseManager


@dataclass
class RegisteredModel:
    id: int
    model_name: str
    version: str
    detector_name: str
    recognizer_name: str
    local_path: str
    sha256: Optional[str]
    is_active: bool
    installed_at: str


class SettingsRepository:
    """Manages application key-value settings and registered models."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting by key."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT value FROM application_settings WHERE key = ?", (key,))
        row = cur.fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        """Set a setting by key."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO application_settings (key, value, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = excluded.updated_at
                """,
                (key, value, now_str),
            )

    def register_model(
        self,
        model_name: str,
        version: str,
        detector_name: str,
        recognizer_name: str,
        local_path: str,
        sha256: Optional[str] = None,
        is_active: bool = True,
    ) -> int:
        """Register an installed AI model package."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            if is_active:
                cur.execute("UPDATE model_registry SET is_active = 0")
            cur.execute(
                """
                INSERT INTO model_registry (
                    model_name, version, detector_name, recognizer_name,
                    local_path, sha256, is_active, installed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    model_name,
                    version,
                    detector_name,
                    recognizer_name,
                    local_path,
                    sha256,
                    1 if is_active else 0,
                    now_str,
                ),
            )
            return cur.lastrowid

    def get_active_model(self) -> Optional[RegisteredModel]:
        """Fetch the currently active model."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, model_name, version, detector_name, recognizer_name,
                   local_path, sha256, is_active, installed_at
            FROM model_registry
            WHERE is_active = 1
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
        if not row:
            return None
        return RegisteredModel(
            id=row["id"],
            model_name=row["model_name"],
            version=row["version"],
            detector_name=row["detector_name"],
            recognizer_name=row["recognizer_name"],
            local_path=row["local_path"],
            sha256=row["sha256"],
            is_active=bool(row["is_active"]),
            installed_at=row["installed_at"],
        )
