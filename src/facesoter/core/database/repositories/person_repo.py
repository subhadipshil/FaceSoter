"""
Repository for Person profiles and reference face samples.
"""

from __future__ import annotations
import uuid
import json
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple
import numpy as np
from facesoter.core.database.db_manager import DatabaseManager


@dataclass
class ReferenceFace:
    id: int
    person_id: int
    image_path: str
    bbox: List[float]
    landmarks: Optional[List[List[float]]]
    embedding: np.ndarray
    thumbnail_path: Optional[str]
    created_at: str


@dataclass
class Person:
    id: int
    uuid: str
    display_name: str
    notes: Optional[str]
    created_at: str
    updated_at: str
    sample_count: int = 0
    reference_faces: Optional[List[ReferenceFace]] = None


class PersonRepository:
    """Handles CRUD operations for enrolled people and reference faces."""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def create_person(self, display_name: str, notes: Optional[str] = None) -> Person:
        """Create a new person profile."""
        now_str = datetime.now(timezone.utc).isoformat()
        p_uuid = str(uuid.uuid4())
        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO people (uuid, display_name, notes, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (p_uuid, display_name.strip(), notes, now_str, now_str),
            )
            person_id = cur.lastrowid
        return Person(
            id=person_id,
            uuid=p_uuid,
            display_name=display_name.strip(),
            notes=notes,
            created_at=now_str,
            updated_at=now_str,
            sample_count=0,
            reference_faces=[],
        )

    def get_person_by_id(self, person_id: int, include_faces: bool = False) -> Optional[Person]:
        """Fetch a person by database ID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.uuid, p.display_name, p.notes, p.created_at, p.updated_at,
                   COUNT(rf.id) as sample_count
            FROM people p
            LEFT JOIN person_reference_faces rf ON p.id = rf.person_id
            WHERE p.id = ?
            GROUP BY p.id
            """,
            (person_id,),
        )
        row = cur.fetchone()
        if not row:
            return None
        person = Person(
            id=row["id"],
            uuid=row["uuid"],
            display_name=row["display_name"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            sample_count=row["sample_count"],
        )
        if include_faces:
            person.reference_faces = self.get_reference_faces(person_id)
        return person

    def get_person_by_uuid(self, p_uuid: str) -> Optional[Person]:
        """Fetch a person by UUID."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.uuid, p.display_name, p.notes, p.created_at, p.updated_at,
                   COUNT(rf.id) as sample_count
            FROM people p
            LEFT JOIN person_reference_faces rf ON p.id = rf.person_id
            WHERE p.uuid = ?
            GROUP BY p.id
            """,
            (p_uuid,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Person(
            id=row["id"],
            uuid=row["uuid"],
            display_name=row["display_name"],
            notes=row["notes"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            sample_count=row["sample_count"],
        )

    def list_people(self) -> List[Person]:
        """List all enrolled people with their sample counts."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT p.id, p.uuid, p.display_name, p.notes, p.created_at, p.updated_at,
                   COUNT(rf.id) as sample_count
            FROM people p
            LEFT JOIN person_reference_faces rf ON p.id = rf.person_id
            GROUP BY p.id
            ORDER BY p.display_name ASC
            """
        )
        people = []
        for row in cur.fetchall():
            people.append(
                Person(
                    id=row["id"],
                    uuid=row["uuid"],
                    display_name=row["display_name"],
                    notes=row["notes"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                    sample_count=row["sample_count"],
                )
            )
        return people

    def update_person_name(self, person_id: int, new_name: str) -> None:
        """Rename a person profile."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            cur.execute(
                "UPDATE people SET display_name = ?, updated_at = ? WHERE id = ?",
                (new_name.strip(), now_str, person_id),
            )

    def delete_person(self, person_id: int) -> None:
        """Delete a person profile and associated references."""
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM people WHERE id = ?", (person_id,))

    def add_reference_face(
        self,
        person_id: int,
        image_path: str,
        bbox: List[float],
        embedding: np.ndarray,
        landmarks: Optional[List[List[float]]] = None,
        thumbnail_path: Optional[str] = None,
    ) -> int:
        """Add a reference face sample to a person profile."""
        now_str = datetime.now(timezone.utc).isoformat()
        bbox_json = json.dumps(bbox)
        landmarks_json = json.dumps(landmarks) if landmarks else None
        emb_bytes = np.asarray(embedding, dtype=np.float32).tobytes()

        with self.db.transaction() as cur:
            cur.execute(
                """
                INSERT INTO person_reference_faces (
                    person_id, image_path, bbox_json, landmarks_json,
                    embedding_blob, thumbnail_path, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    person_id,
                    image_path,
                    bbox_json,
                    landmarks_json,
                    emb_bytes,
                    thumbnail_path,
                    now_str,
                ),
            )
            face_id = cur.lastrowid
            cur.execute(
                "UPDATE people SET updated_at = ? WHERE id = ?",
                (now_str, person_id),
            )
        return face_id

    def remove_reference_face(self, face_id: int) -> None:
        """Remove a reference face sample."""
        with self.db.transaction() as cur:
            cur.execute("DELETE FROM person_reference_faces WHERE id = ?", (face_id,))

    def get_reference_faces(self, person_id: int) -> List[ReferenceFace]:
        """Get all reference face samples for a person."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, person_id, image_path, bbox_json, landmarks_json,
                   embedding_blob, thumbnail_path, created_at
            FROM person_reference_faces
            WHERE person_id = ?
            ORDER BY id ASC
            """,
            (person_id,),
        )
        faces = []
        for row in cur.fetchall():
            emb = np.frombuffer(row["embedding_blob"], dtype=np.float32)
            bbox = json.loads(row["bbox_json"])
            lm = json.loads(row["landmarks_json"]) if row["landmarks_json"] else None
            faces.append(
                ReferenceFace(
                    id=row["id"],
                    person_id=row["person_id"],
                    image_path=row["image_path"],
                    bbox=bbox,
                    landmarks=lm,
                    embedding=emb,
                    thumbnail_path=row["thumbnail_path"],
                    created_at=row["created_at"],
                )
            )
        return faces

    def get_all_reference_embeddings(self) -> Dict[int, List[np.ndarray]]:
        """Fetch all reference embeddings grouped by person_id."""
        conn = self.db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT person_id, embedding_blob FROM person_reference_faces")
        result: Dict[int, List[np.ndarray]] = {}
        for row in cur.fetchall():
            pid = row["person_id"]
            emb = np.frombuffer(row["embedding_blob"], dtype=np.float32)
            result.setdefault(pid, []).append(emb)
        return result

    def merge_people(self, target_person_id: int, source_person_id: int) -> None:
        """Merge source person into target person, reassigning reference faces and detections."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.transaction() as cur:
            # Move reference faces
            cur.execute(
                "UPDATE person_reference_faces SET person_id = ? WHERE person_id = ?",
                (target_person_id, source_person_id),
            )
            # Move detection assignments
            cur.execute(
                "UPDATE image_faces SET assigned_person_id = ? WHERE assigned_person_id = ?",
                (target_person_id, source_person_id),
            )
            # Update target timestamp
            cur.execute(
                "UPDATE people SET updated_at = ? WHERE id = ?",
                (now_str, target_person_id),
            )
            # Delete source person
            cur.execute("DELETE FROM people WHERE id = ?", (source_person_id,))
