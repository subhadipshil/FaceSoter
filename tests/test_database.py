"""
Unit tests for database manager, schema migrations, and repositories.
"""

import tempfile
from pathlib import Path
import numpy as np
import pytest

from facesoter.core.database.db_manager import DatabaseManager
from facesoter.core.database.repositories import (
    PersonRepository, ImageRepository, JobRepository, SettingsRepository
)


@pytest.fixture
def temp_db():
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_facesoter.db"
        manager = DatabaseManager(db_path)
        yield manager
        manager.close()


def test_schema_initialization(temp_db):
    """Test that all tables and migrations are initialized cleanly."""
    conn = temp_db.get_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r[0] for r in cur.fetchall()}

    expected = {
        "schema_migrations", "people", "person_reference_faces", "images",
        "image_faces", "face_embeddings", "jobs", "job_files",
        "classification_results", "application_settings", "model_registry"
    }
    assert expected.issubset(tables)


def test_person_repository_crud(temp_db):
    """Test PersonRepository create, read, update, delete, and merge."""
    repo = PersonRepository(temp_db)

    # 1. Create
    p1 = repo.create_person("Alice", notes="Friend")
    p2 = repo.create_person("Bob")
    assert p1.id is not None
    assert p1.display_name == "Alice"
    assert len(p1.uuid) == 36

    # 2. Read
    fetched = repo.get_person_by_id(p1.id)
    assert fetched is not None
    assert fetched.display_name == "Alice"
    assert fetched.notes == "Friend"

    # 3. Add reference faces
    dummy_emb = np.random.randn(512).astype(np.float32)
    dummy_emb /= np.linalg.norm(dummy_emb)
    f_id = repo.add_reference_face(
        person_id=p1.id,
        image_path="/path/to/alice.jpg",
        bbox=[10.0, 20.0, 100.0, 120.0],
        embedding=dummy_emb,
        landmarks=[[30, 40], [70, 40], [50, 60], [40, 80], [60, 80]],
    )
    assert f_id > 0

    refs = repo.get_reference_faces(p1.id)
    assert len(refs) == 1
    assert np.allclose(refs[0].embedding, dummy_emb)
    assert refs[0].bbox == [10.0, 20.0, 100.0, 120.0]

    # 4. Rename
    repo.update_person_name(p1.id, "Alice Smith")
    assert repo.get_person_by_id(p1.id).display_name == "Alice Smith"

    # 5. Merge p2 into p1
    dummy_emb2 = np.random.randn(512).astype(np.float32)
    dummy_emb2 /= np.linalg.norm(dummy_emb2)
    repo.add_reference_face(
        person_id=p2.id,
        image_path="/path/to/bob.jpg",
        bbox=[15.0, 25.0, 105.0, 125.0],
        embedding=dummy_emb2,
    )
    repo.merge_people(target_person_id=p1.id, source_person_id=p2.id)

    assert repo.get_person_by_id(p2.id) is None
    merged_refs = repo.get_reference_faces(p1.id)
    assert len(merged_refs) == 2

    # 6. Delete
    repo.delete_person(p1.id)
    assert repo.get_person_by_id(p1.id) is None


def test_image_and_faces_repository(temp_db):
    """Test ImageRepository storing images, faces, and embeddings."""
    repo = ImageRepository(temp_db)

    # 1. Upsert image
    img_id = repo.upsert_image(
        file_path="/photos/img001.jpg",
        file_size=1024000,
        modified_time=1700000000.0,
        file_hash="hash123",
        width=1920,
        height=1080,
    )
    assert img_id > 0

    # 2. Add detected faces
    emb1 = np.ones(512, dtype=np.float32) / np.sqrt(512)
    f1 = repo.add_detected_face(
        image_id=img_id,
        bbox=[50, 50, 200, 200],
        det_score=0.98,
        embedding=emb1,
        thumbnail_path="/thumbs/t1.jpg",
    )
    assert f1 > 0

    # 3. Retrieve faces
    faces = repo.get_faces_for_image(img_id, load_embedding=True)
    assert len(faces) == 1
    assert faces[0].det_score == 0.98
    assert faces[0].thumbnail_path == "/thumbs/t1.jpg"
    assert np.allclose(faces[0].embedding, emb1)


def test_job_persistence_and_recovery(temp_db):
    """Test JobRepository checkpointing and crash recovery."""
    repo = JobRepository(temp_db)

    # Create job
    job = repo.create_job(
        name="Test Scan",
        mode="categorization",
        source_dir="/photos/src",
        export_dir="/photos/dst",
    )
    assert job.status == "queued"

    # Add files
    file_list = [f"/photos/src/img_{i}.jpg" for i in range(10)]
    repo.set_job_total_files(job.id, 10)
    repo.add_job_files(job.id, file_list)

    # Simulate processing first 4 files
    batch = repo.get_pending_job_files(job.id, limit=4)
    assert len(batch) == 4

    for bf in batch:
        repo.update_job_file_status(job.id, bf.file_path, "completed")

    repo.update_job_progress(job.id, processed_files=4, failed_files=0, faces_detected=6, copied_files=0)
    repo.update_job_status(job.id, "running")

    # Simulate app crash & restart: recover interrupted jobs
    recovered = repo.recover_interrupted_jobs()
    assert recovered == 1

    updated_job = repo.get_job(job.id)
    assert updated_job.status == "interrupted"

    # Next batch on resume should only fetch remaining 6 files
    remaining = repo.get_pending_job_files(job.id, limit=10)
    assert len(remaining) == 6
    assert all(rf.file_path not in [b.file_path for b in batch] for rf in remaining)
