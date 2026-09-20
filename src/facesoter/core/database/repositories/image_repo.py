"""
Repository for scanned images, detected faces, and embeddings.
"""

from __future__ import annotations
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict
import numpy as np
from facesoter.core.database.db_manager import DatabaseManager


@dataclass
class DetectedFaceRecord:
    id: int
    image_id: int
    bbox: List[float]  # [x1, y1, x2, y2]
    det_score: float
    face_size: float
    landmarks: Optional[List[List[float]]]
    assigned_person_id: Optional[int]
    assigned_cluster_id: Optional[str]
    confidence: Optional[float]
    thumbnail_path: Optional[str]
    embedding: Optional[np.ndarray] = None


@dataclass
class ImageRecord:
    id: int
    file_path: str
    file_hash: Optional[str]
    file_size: int
    width: Optional[int]
    height: Optional[int]
    modified_time: float
    face_count: int
    status: str
    error_message: Optional[str]
    created_at: str
    processed_at: Optional[str]
    faces: Optional[List[DetectedFaceRecord]] = None


class ImageRepository:
    """Handles storage and retrieval of image scans, faces, and embeddings."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def upsert_image(
        self,
        file_path: str,
        file_size: int,
        modified_time: float,
        file_hash: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> int:
        """Insert or retrieve an image record."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO images (
                    file_path, file_hash, file_size, width, height,
                    modified_time, status, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
                ON CONFLICT(file_path) DO UPDATE SET
                    file_size = excluded.file_size,
                    modified_time = excluded.modified_time,
                    file_hash = COALESCE(excluded.file_hash, images.file_hash),
                    width = COALESCE(excluded.width, images.width),
                    height = COALESCE(excluded.height, images.height)
                """,
                (file_path, file_hash, file_size, width, height, modified_time, now_str),
            )
            cur.execute("SELECT id FROM images WHERE file_path = ?", (file_path,))
            row = cur.fetchone()
            return row["id"]

    def get_image_by_path(self, file_path: str) -> Optional[ImageRecord]:
        """Fetch image record by path."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, file_path, file_hash, file_size, width, height,
                   modified_time, face_count, status, error_message,
                   created_at, processed_at
            FROM images WHERE file_path = ?
            """,
            (file_path,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return ImageRecord(
            id=row["id"],
            file_path=row["file_path"],
            file_hash=row["file_hash"],
            file_size=row["file_size"],
            width=row["width"],
            height=row["height"],
            modified_time=row["modified_time"],
            face_count=row["face_count"],
            status=row["status"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            processed_at=row["processed_at"],
        )

    def mark_image_processed(
        self,
        image_id: int,
        face_count: int,
        status: str = "processed",
        error_message: Optional[str] = None,
    ) -> None:
        """Update processed status of an image."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                """
                UPDATE images
                SET face_count = ?, status = ?, error_message = ?, processed_at = ?
                WHERE id = ?
                """,
                (face_count, status, error_message, now_str, image_id),
            )

    def add_detected_face(
        self,
        image_id: int,
        bbox: List[float],
        det_score: float,
        embedding: np.ndarray,
        landmarks: Optional[List[List[float]]] = None,
        assigned_person_id: Optional[int] = None,
        assigned_cluster_id: Optional[str] = None,
        confidence: Optional[float] = None,
        thumbnail_path: Optional[str] = None,
    ) -> int:
        """Record a detected face and its 512-d normalized embedding."""
        landmarks_json = json.dumps(landmarks) if landmarks else None
        emb_bytes = np.asarray(embedding, dtype=np.float32).tobytes()
        face_size = max(bbox[2] - bbox[0], bbox[3] - bbox[1])

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO image_faces (
                    image_id, bbox_x1, bbox_y1, bbox_x2, bbox_y2,
                    det_score, face_size, landmarks_json, assigned_person_id,
                    assigned_cluster_id, confidence, thumbnail_path
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    image_id,
                    bbox[0],
                    bbox[1],
                    bbox[2],
                    bbox[3],
                    det_score,
                    face_size,
                    landmarks_json,
                    assigned_person_id,
                    assigned_cluster_id,
                    confidence,
                    thumbnail_path,
                ),
            )
            face_id = cur.lastrowid
            cur.execute(
                """
                INSERT INTO face_embeddings (face_id, dim, norm, embedding_blob)
                VALUES (?, 512, 1.0, ?)
                """,
                (face_id, emb_bytes),
            )
            return face_id

    def get_faces_for_image(self, image_id: int, load_embedding: bool = False) -> List[DetectedFaceRecord]:
        """Fetch all detected faces for a specific image."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        query = """
            SELECT f.id, f.image_id, f.bbox_x1, f.bbox_y1, f.bbox_x2, f.bbox_y2,
                   f.det_score, f.face_size, f.landmarks_json, f.assigned_person_id,
                   f.assigned_cluster_id, f.confidence, f.thumbnail_path
                   {emb_select}
            FROM image_faces f
            {emb_join}
            WHERE f.image_id = ?
            ORDER BY f.id ASC
        """
        if load_embedding:
            query = query.format(
                emb_select=", fe.embedding_blob",
                emb_join="LEFT JOIN face_embeddings fe ON f.id = fe.face_id",
            )
        else:
            query = query.format(emb_select="", emb_join="")

        cur.execute(query, (image_id,))
        faces = []
        for row in cur.fetchall():
            emb = None
            if load_embedding and row["embedding_blob"] is not None:
                emb = np.frombuffer(row["embedding_blob"], dtype=np.float32)
            lm = json.loads(row["landmarks_json"]) if row["landmarks_json"] else None
            faces.append(
                DetectedFaceRecord(
                    id=row["id"],
                    image_id=row["image_id"],
                    bbox=[row["bbox_x1"], row["bbox_y1"], row["bbox_x2"], row["bbox_y2"]],
                    det_score=row["det_score"],
                    face_size=row["face_size"],
                    landmarks=lm,
                    assigned_person_id=row["assigned_person_id"],
                    assigned_cluster_id=row["assigned_cluster_id"],
                    confidence=row["confidence"],
                    thumbnail_path=row["thumbnail_path"],
                    embedding=emb,
                )
            )
        return faces

    def assign_face_person(self, face_id: int, person_id: Optional[int], confidence: Optional[float] = None) -> None:
        """Assign or reassign a detected face to an enrolled person profile."""
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE image_faces SET assigned_person_id = ?, confidence = ? WHERE id = ?",
                (person_id, confidence, face_id),
            )

    def assign_face_cluster(self, face_id: int, cluster_id: Optional[str]) -> None:
        """Assign or reassign a detected face to an unknown person cluster."""
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE image_faces SET assigned_cluster_id = ? WHERE id = ?",
                (cluster_id, face_id),
            )

    def get_unassigned_faces_for_job(self, job_id: int) -> List[Tuple[int, np.ndarray]]:
        """Get list of (face_id, embedding) for faces in a job not assigned to known person."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT f.id, fe.embedding_blob
            FROM image_faces f
            JOIN face_embeddings fe ON f.id = fe.face_id
            JOIN images img ON f.image_id = img.id
            JOIN job_files jf ON img.id = jf.image_id
            WHERE jf.job_id = ? AND f.assigned_person_id IS NULL
            """,
            (job_id,),
        )
        results = []
        for row in cur.fetchall():
            emb = np.frombuffer(row["embedding_blob"], dtype=np.float32)
            results.append((row["id"], emb))
        return results
