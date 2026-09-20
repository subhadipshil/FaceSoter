"""
Integration tests for the complete ScanPipeline and OrganizerEngine.
"""

import tempfile
from pathlib import Path
from typing import List
import numpy as np
import pytest
from PIL import Image

from facesoter.core.ai.provider import FaceDetectionProvider, FaceEmbeddingProvider, DetectedFace
from facesoter.core.ai.matcher import FaceMatcher
from facesoter.core.ai.clusterer import FaceClusterer
from facesoter.core.database.db_manager import DatabaseManager
from facesoter.core.database.repositories import (
    PersonRepository, ImageRepository, JobRepository
)
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache
from facesoter.core.organizer.engine import OrganizerEngine
from facesoter.core.jobs.pipeline import ScanPipeline


class SyntheticAIProvider(FaceDetectionProvider, FaceEmbeddingProvider):
    """Synthetic provider generating deterministic faces and embeddings for integration testing."""

    def __init__(self):
        # Deterministic embeddings for test identities
        np.random.seed(1234)
        self.mom_emb = np.random.randn(512).astype(np.float32)
        self.mom_emb /= np.linalg.norm(self.mom_emb)

        self.dad_emb = np.random.randn(512).astype(np.float32)
        self.dad_emb /= np.linalg.norm(self.dad_emb)

        self.unknown_emb = np.random.randn(512).astype(np.float32)
        self.unknown_emb /= np.linalg.norm(self.unknown_emb)

    def detect_faces(self, image_bgr: np.ndarray, threshold: float = 0.5, min_size: int = 32) -> List[DetectedFace]:
        # Identify image by height/width or filename patterns encoded in size
        h, w = image_bgr.shape[:2]

        if w == 100 and h == 100:
            # No-face image
            return []
        elif w == 200 and h == 200:
            # Single-person image: Mom
            return [DetectedFace(bbox=(20, 20, 80, 80), score=0.96)]
        elif w == 300 and h == 300:
            # Two-person image: Mom + Dad
            return [
                DetectedFace(bbox=(20, 20, 80, 80), score=0.95),
                DetectedFace(bbox=(120, 20, 180, 80), score=0.93),
            ]
        elif w == 400 and h == 400:
            # Unknown recurring person
            return [DetectedFace(bbox=(30, 30, 90, 90), score=0.91)]
        return []

    def compute_embedding(self, image_bgr: np.ndarray, face: DetectedFace) -> np.ndarray:
        h, w = image_bgr.shape[:2]
        x1 = face.bbox[0]
        if w == 200:
            return self.mom_emb.copy()
        elif w == 300:
            if x1 < 100:
                return self.mom_emb.copy()
            else:
                return self.dad_emb.copy()
        elif w == 400:
            # Add tiny noise to unknown identity
            noise = np.random.randn(512).astype(np.float32) * 0.05
            emb = self.unknown_emb + noise
            return emb / np.linalg.norm(emb)
        return np.zeros(512, dtype=np.float32)

    def compute_embeddings_batch(self, image_bgr: np.ndarray, faces: List[DetectedFace]) -> List[np.ndarray]:
        return [self.compute_embedding(image_bgr, f) for f in faces]


@pytest.fixture
def integration_env():
    with tempfile.TemporaryDirectory() as src_dir, \
         tempfile.TemporaryDirectory() as exp_dir, \
         tempfile.TemporaryDirectory() as app_dir:

        src = Path(src_dir)
        exp = Path(exp_dir)
        app = Path(app_dir)

        # Create test images
        # 1. No face (100x100)
        Image.new("RGB", (100, 100), color="blue").save(src / "scenery_no_face.jpg")

        # 2. Mom solo (200x200)
        Image.new("RGB", (200, 200), color="red").save(src / "mom_solo.jpg")

        # 3. Mom + Dad (300x300)
        Image.new("RGB", (300, 300), color="green").save(src / "mom_and_dad.jpg")

        # 4 & 5. Unknown recurring person (400x400)
        Image.new("RGB", (400, 400), color="yellow").save(src / "unknown_photo1.jpg")
        Image.new("RGB", (400, 400), color="purple").save(src / "unknown_photo2.jpg")

        # Database & Cache
        db = DatabaseManager(app / "test.db")
        person_repo = PersonRepository(db)
        image_repo = ImageRepository(db)
        job_repo = JobRepository(db)
        thumb_cache = ThumbnailCache(app / "thumbs")
        ai = SyntheticAIProvider()

        # Enroll Mom and Dad in database
        mom = person_repo.create_person("Mom")
        person_repo.add_reference_face(mom.id, "ref_mom.jpg", [0, 0, 10, 10], ai.mom_emb)

        dad = person_repo.create_person("Dad")
        person_repo.add_reference_face(dad.id, "ref_dad.jpg", [0, 0, 10, 10], ai.dad_emb)

        pipeline = ScanPipeline(
            job_repo=job_repo,
            image_repo=image_repo,
            person_repo=person_repo,
            detector=ai,
            embedder=ai,
            thumbnail_cache=thumb_cache,
            matcher=FaceMatcher(threshold=0.60),
            clusterer=FaceClusterer(similarity_threshold=0.60),
        )

        organizer = OrganizerEngine(job_repo=job_repo, image_repo=image_repo)

        yield {
            "src": src,
            "exp": exp,
            "pipeline": pipeline,
            "organizer": organizer,
            "job_repo": job_repo,
            "person_repo": person_repo,
            "mom_id": mom.id,
            "dad_id": dad.id,
        }
        db.close()


def test_full_categorization_pipeline(integration_env):
    """Test full scan and copy for Mode A Categorization."""
    env = integration_env
    job_repo: JobRepository = env["job_repo"]
    pipeline: ScanPipeline = env["pipeline"]
    organizer: OrganizerEngine = env["organizer"]

    job = job_repo.create_job(
        name="Test Categorization",
        mode="categorization",
        source_dir=str(env["src"]),
        export_dir=str(env["exp"]),
    )

    success = pipeline.run_pipeline(job.id, batch_size=2)
    assert success is True

    # Check database classification results
    classifications = job_repo.get_classification_results(job.id)
    dest_map = {c.destination_path: c.target_category for c in classifications}

    # Verify:
    # 1. No face photo routed to Uncategorized/No Face
    assert "Uncategorized/No Face" in dest_map

    # 2. Mom and Dad folders exist
    assert "Categorized/Mom" in dest_map
    assert "Categorized/Dad" in dest_map

    # 3. Unknown cluster exists
    unknown_folder = [k for k in dest_map.keys() if "Person 001" in k]
    assert len(unknown_folder) > 0

    # 4. Generate Pre-Copy Summary
    summary = organizer.generate_preview(job.id)
    assert summary.photos_scanned == 5
    assert summary.photos_without_faces == 1
    assert summary.photos_with_faces == 4

    # Execute Copy
    copied, skipped, failed = organizer.execute_organization(job.id, env["exp"])
    assert failed == 0
    assert copied > 0

    # Check physical output files on disk
    # Multi-person photo mom_and_dad.jpg MUST exist in BOTH Mom/ and Dad/!
    mom_copy = env["exp"] / "Categorized" / "Mom" / "mom_and_dad.jpg"
    dad_copy = env["exp"] / "Categorized" / "Dad" / "mom_and_dad.jpg"
    assert mom_copy.exists()
    assert dad_copy.exists()

    # No face photo must exist in Uncategorized/No Face/
    no_face_copy = env["exp"] / "Uncategorized" / "No Face" / "scenery_no_face.jpg"
    assert no_face_copy.exists()


def test_full_separation_pipeline(integration_env):
    """Test full scan and copy for Mode B Separation / Filter."""
    env = integration_env
    job_repo: JobRepository = env["job_repo"]
    pipeline: ScanPipeline = env["pipeline"]
    organizer: OrganizerEngine = env["organizer"]

    # Target: ONLY Mom
    job = job_repo.create_job(
        name="Test Separation",
        mode="separation",
        source_dir=str(env["src"]),
        export_dir=str(env["exp"]),
        filter_target_ids=[env["mom_id"]],
    )

    success = pipeline.run_pipeline(job.id, batch_size=2)
    assert success is True

    classifications = job_repo.get_classification_results(job.id)
    destinations = [c.destination_path for c in classifications]

    # Only photos containing Mom (mom_solo and mom_and_dad) should be planned
    assert all("SeparateFilter/Mom" in d for d in destinations)
    assert len(destinations) == 2

    # Execute Copy
    copied, skipped, failed = organizer.execute_organization(job.id, env["exp"])
    assert failed == 0
    assert copied == 2

    assert (env["exp"] / "SeparateFilter" / "Mom" / "mom_solo.jpg").exists()
    assert (env["exp"] / "SeparateFilter" / "Mom" / "mom_and_dad.jpg").exists()

    # Strict separation rule: No photos should leak into Categorized/ or No Face!
    assert not (env["exp"] / "Categorized").exists()
    assert not (env["exp"] / "Uncategorized").exists()
