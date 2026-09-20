"""
Repository for Jobs, Job Files, and Classification Results with Checkpointing.
"""

from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from facesoter.core.database.db_manager import DatabaseManager


@dataclass
class JobRecord:
    id: int
    uuid: str
    name: str
    mode: str  # "categorization" or "separation"
    source_dir: str
    export_dir: str
    status: str  # "queued", "running", "paused", "completed", "cancelled", "failed", "interrupted"
    include_subfolders: bool
    settings_json: str
    filter_target_ids_json: Optional[str]
    total_files: int
    processed_files: int
    failed_files: int
    faces_detected: int
    copied_files: int
    created_at: str
    updated_at: str
    completed_at: Optional[str]


@dataclass
class JobFileRecord:
    id: int
    job_id: int
    image_id: Optional[int]
    file_path: str
    status: str  # "pending", "processing", "completed", "failed", "skipped"
    error_message: Optional[str]
    updated_at: str


@dataclass
class ClassificationRecord:
    id: int
    job_id: int
    image_id: int
    target_category: str
    destination_path: str
    copy_status: str  # "pending", "copied", "failed", "skipped"
    error_message: Optional[str]
    created_at: str


class JobRepository:
    """Handles persistence for scanning, organization jobs, and checkpoint resume."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_job(
        self,
        name: str,
        mode: str,
        source_dir: str,
        export_dir: str,
        include_subfolders: bool = True,
        settings_dict: Optional[Dict[str, Any]] = None,
        filter_target_ids: Optional[List[int]] = None,
    ) -> JobRecord:
        """Create a new job record."""
        now_str = datetime.now(timezone.utc).isoformat()
        job_uuid = str(uuid.uuid4())
        settings_json = json.dumps(settings_dict or {})
        target_ids_json = json.dumps(filter_target_ids) if filter_target_ids else None

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO jobs (
                    uuid, name, mode, source_dir, export_dir, status,
                    include_subfolders, settings_json, filter_target_ids_json,
                    total_files, processed_files, failed_files, faces_detected,
                    copied_files, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, 'queued', ?, ?, ?, 0, 0, 0, 0, 0, ?, ?)
                """,
                (
                    job_uuid,
                    name,
                    mode,
                    source_dir,
                    export_dir,
                    1 if include_subfolders else 0,
                    settings_json,
                    target_ids_json,
                    now_str,
                    now_str,
                ),
            )
            job_id = cur.lastrowid

        return JobRecord(
            id=job_id,
            uuid=job_uuid,
            name=name,
            mode=mode,
            source_dir=source_dir,
            export_dir=export_dir,
            status="queued",
            include_subfolders=include_subfolders,
            settings_json=settings_json,
            filter_target_ids_json=target_ids_json,
            total_files=0,
            processed_files=0,
            failed_files=0,
            faces_detected=0,
            copied_files=0,
            created_at=now_str,
            updated_at=now_str,
            completed_at=None,
        )

    def get_job(self, job_id: int) -> Optional[JobRecord]:
        """Fetch job by ID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, uuid, name, mode, source_dir, export_dir, status,
                   include_subfolders, settings_json, filter_target_ids_json,
                   total_files, processed_files, failed_files, faces_detected,
                   copied_files, created_at, updated_at, completed_at
            FROM jobs WHERE id = ?
            """,
            (job_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def get_job_by_uuid(self, job_uuid: str) -> Optional[JobRecord]:
        """Fetch job by UUID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, uuid, name, mode, source_dir, export_dir, status,
                   include_subfolders, settings_json, filter_target_ids_json,
                   total_files, processed_files, failed_files, faces_detected,
                   copied_files, created_at, updated_at, completed_at
            FROM jobs WHERE uuid = ?
            """,
            (job_uuid,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return self._row_to_job(row)

    def list_jobs(self, limit: int = 50) -> List[JobRecord]:
        """List recent jobs."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, uuid, name, mode, source_dir, export_dir, status,
                   include_subfolders, settings_json, filter_target_ids_json,
                   total_files, processed_files, failed_files, faces_detected,
                   copied_files, created_at, updated_at, completed_at
            FROM jobs
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        return [self._row_to_job(r) for r in cur.fetchall()]

    def update_job_status(self, job_id: int, status: str, completed: bool = False) -> None:
        """Update job lifecycle status."""
        now_str = datetime.now(timezone.utc).isoformat()
        completed_at = now_str if completed else None
        with self.db.transaction() as cur:
            if completed:
                cur.execute(
                    "UPDATE jobs SET status = ?, updated_at = ?, completed_at = ? WHERE id = ?",
                    (status, now_str, completed_at, job_id),
                )
            else:
                cur.execute(
                    "UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?",
                    (status, now_str, job_id),
                )

    def update_job_progress(
        self,
        job_id: int,
        processed_files: int,
        failed_files: int,
        faces_detected: int,
        copied_files: int,
    ) -> None:
        """Update live processing counters."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                UPDATE jobs
                SET processed_files = ?, failed_files = ?,
                    faces_detected = ?, copied_files = ?, updated_at = ?
                WHERE id = ?
                """,
                (processed_files, failed_files, faces_detected, copied_files, now_str, job_id),
            )

    def set_job_total_files(self, job_id: int, total_files: int) -> None:
        """Set total discovered files count."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE jobs SET total_files = ?, updated_at = ? WHERE id = ?",
                (total_files, now_str, job_id),
            )

    def add_job_files(self, job_id: int, file_paths: List[str]) -> None:
        """Add scanned file paths to job_files in batch."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.executemany(
                """
                INSERT OR IGNORE INTO job_files (job_id, file_path, status, updated_at)
                VALUES (?, ?, 'pending', ?)
                """,
                [(job_id, fp, now_str) for fp in file_paths],
            )

    def get_pending_job_files(self, job_id: int, limit: int = 50) -> List[JobFileRecord]:
        """Fetch batch of uncompleted files for a job (supports checkpoint resume)."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, job_id, image_id, file_path, status, error_message, updated_at
            FROM job_files
            WHERE job_id = ? AND status IN ('pending', 'failed_retry')
            ORDER BY id ASC
            LIMIT ?
            """,
            (job_id, limit),
        )
        return [
            JobFileRecord(
                id=r["id"],
                job_id=r["job_id"],
                image_id=r["image_id"],
                file_path=r["file_path"],
                status=r["status"],
                error_message=r["error_message"],
                updated_at=r["updated_at"],
            )
            for r in cur.fetchall()
        ]

    def update_job_file_status(
        self,
        job_id: int,
        file_path: str,
        status: str,
        image_id: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Update status of a specific file in a job."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                UPDATE job_files
                SET status = ?, image_id = COALESCE(?, image_id),
                    error_message = ?, updated_at = ?
                WHERE job_id = ? AND file_path = ?
                """,
                (status, image_id, error_message, now_str, job_id, file_path),
            )

    def record_classification_result(
        self,
        job_id: int,
        image_id: int,
        target_category: str,
        destination_path: str,
        copy_status: str = "pending",
        error_message: Optional[str] = None,
    ) -> int:
        """Record a planned or executed file organization destination."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO classification_results (
                    job_id, image_id, target_category, destination_path,
                    copy_status, error_message, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    image_id,
                    target_category,
                    destination_path,
                    copy_status,
                    error_message,
                    now_str,
                ),
            )
            return cur.lastrowid

    def get_classification_results(self, job_id: int) -> List[ClassificationRecord]:
        """Fetch all planned/executed file classifications for a job."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, job_id, image_id, target_category, destination_path,
                   copy_status, error_message, created_at
            FROM classification_results
            WHERE job_id = ?
            ORDER BY id ASC
            """,
            (job_id,),
        )
        return [
            ClassificationRecord(
                id=r["id"],
                job_id=r["job_id"],
                image_id=r["image_id"],
                target_category=r["target_category"],
                destination_path=r["destination_path"],
                copy_status=r["copy_status"],
                error_message=r["error_message"],
                created_at=r["created_at"],
            )
            for r in cur.fetchall()
        ]

    def update_classification_copy_status(
        self, result_id: int, copy_status: str, error_message: Optional[str] = None
    ) -> None:
        """Update file copy execution status."""
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE classification_results SET copy_status = ?, error_message = ? WHERE id = ?",
                (copy_status, error_message, result_id),
            )

    def get_failed_files(self, job_id: int) -> List[Dict[str, Any]]:
        """Get all failed files and reasons for a job."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT file_path, status, error_message, updated_at
            FROM job_files
            WHERE job_id = ? AND status = 'failed'
            ORDER BY id ASC
            """,
            (job_id,),
        )
        return [dict(r) for r in cur.fetchall()]

    def recover_interrupted_jobs(self) -> int:
        """Mark any jobs that were left running as 'interrupted' on app startup."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                UPDATE jobs
                SET status = 'interrupted', updated_at = ?
                WHERE status = 'running'
                """,
                (now_str,),
            )
            return cur.rowcount

    def _row_to_job(self, r) -> JobRecord:
        return JobRecord(
            id=r["id"],
            uuid=r["uuid"],
            name=r["name"],
            mode=r["mode"],
            source_dir=r["source_dir"],
            export_dir=r["export_dir"],
            status=r["status"],
            include_subfolders=bool(r["include_subfolders"]),
            settings_json=r["settings_json"],
            filter_target_ids_json=r["filter_target_ids_json"],
            total_files=r["total_files"],
            processed_files=r["processed_files"],
            failed_files=r["failed_files"],
            faces_detected=r["faces_detected"],
            copied_files=r["copied_files"],
            created_at=r["created_at"],
            updated_at=r["updated_at"],
            completed_at=r["completed_at"],
        )
