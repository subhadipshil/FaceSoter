"""
Core processing pipeline: discovery -> detection -> embedding -> matching -> clustering -> organization planning.
"""

from __future__ import annotations
import time
from pathlib import Path
from typing import Callable, Optional, Dict, List, Set, Tuple
from dataclasses import dataclass
import numpy as np

from facesoter.core.ai.provider import FaceDetectionProvider, FaceEmbeddingProvider, DetectedFace
from facesoter.core.ai.matcher import FaceMatcher
from facesoter.core.ai.clusterer import FaceClusterer, FaceCluster
from facesoter.core.scanner.file_scanner import FileScanner
from facesoter.core.scanner.image_reader import ImageReader
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache
from facesoter.core.organizer.rule_engine import OrganizationRuleEngine, PlannedDestination
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord
from facesoter.core.database.repositories.image_repo import ImageRepository
from facesoter.core.database.repositories.person_repo import PersonRepository
from facesoter.core.logging.logger import get_logger

logger = get_logger("pipeline")


@dataclass
class PipelineProgress:
    phase: str  # "discovery", "detection", "matching", "clustering", "planning", "completed"
    current_file: str
    processed_files: int
    total_files: int
    faces_detected: int
    known_matches: int
    unknown_clusters: int
    no_face_count: int
    failed_files: int
    speed: float  # items/sec
    elapsed_seconds: float
    remaining_seconds: float


class ScanPipeline:
    """Executes end-to-end scanning, face recognition, and organization planning."""

    def __init__(
        self,
        job_repo: JobRepository,
        image_repo: ImageRepository,
        person_repo: PersonRepository,
        detector: FaceDetectionProvider,
        embedder: FaceEmbeddingProvider,
        thumbnail_cache: ThumbnailCache,
        matcher: Optional[FaceMatcher] = None,
        clusterer: Optional[FaceClusterer] = None,
    ):
        self.job_repo = job_repo
        self.image_repo = image_repo
        self.person_repo = person_repo
        self.detector = detector
        self.embedder = embedder
        self.thumbnail_cache = thumbnail_cache
        self.matcher = matcher or FaceMatcher(threshold=0.50)
        self.clusterer = clusterer or FaceClusterer(similarity_threshold=0.55)

    def run_pipeline(
        self,
        job_id: int,
        batch_size: int = 32,
        progress_callback: Optional[Callable[[PipelineProgress], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
        pause_check: Optional[Callable[[], bool]] = None,
    ) -> bool:
        """Run or resume the pipeline for a job."""
        job = self.job_repo.get_job(job_id)
        if not job:
            raise ValueError(f"Job #{job_id} not found.")

        start_time = time.time()
        self.job_repo.update_job_status(job_id, "running")

        try:
            # 1. Discovery Phase (if job has 0 total files or is fresh)
            if job.total_files == 0:
                logger.info(f"Starting discovery for Job #{job_id} at {job.source_dir}")
                scanner = FileScanner(include_subfolders=job.include_subfolders)
                discovered = scanner.collect_files(job.source_dir, cancel_check)
                if cancel_check and cancel_check():
                    self.job_repo.update_job_status(job_id, "cancelled")
                    return False

                self.job_repo.set_job_total_files(job_id, len(discovered))
                self.job_repo.add_job_files(job_id, [str(p) for p in discovered])
                job = self.job_repo.get_job(job_id)
                logger.info(f"Discovered {len(discovered)} files for Job #{job_id}")

            total_files = job.total_files
            processed = job.processed_files
            failed = job.failed_files
            total_faces = job.faces_detected

            # 2. Batch Processing Phase (checkpoint-safe)
            logger.info(f"Processing image files for Job #{job_id} (batch size {batch_size})...")

            while True:
                if cancel_check and cancel_check():
                    logger.info("Pipeline cancelled.")
                    self.job_repo.update_job_status(job_id, "cancelled")
                    return False

                if pause_check and pause_check():
                    logger.info("Pipeline paused.")
                    self.job_repo.update_job_status(job_id, "paused")
                    return False

                pending_files = self.job_repo.get_pending_job_files(job_id, limit=batch_size)
                if not pending_files:
                    break  # All files processed

                for job_file in pending_files:
                    if cancel_check and cancel_check():
                        self.job_repo.update_job_status(job_id, "cancelled")
                        return False
                    if pause_check and pause_check():
                        self.job_repo.update_job_status(job_id, "paused")
                        return False

                    file_path = job_file.file_path
                    cur_name = Path(file_path).name

                    # Safe image load with EXIF orientation correction
                    img_bgr, width, height, err = ImageReader.load_image_bgr(file_path)

                    if img_bgr is None:
                        failed += 1
                        self.job_repo.update_job_file_status(
                            job_id, file_path, status="failed", error_message=err
                        )
                        processed += 1
                        continue

                    # Upsert image in database
                    try:
                        f_stat = Path(file_path).stat()
                        file_size = f_stat.st_size
                        mod_time = f_stat.st_mtime
                    except Exception:
                        file_size = 0
                        mod_time = 0.0

                    image_id = self.image_repo.upsert_image(
                        file_path=file_path,
                        file_size=file_size,
                        modified_time=mod_time,
                        width=width,
                        height=height,
                    )

                    # Detect faces with SCRFD
                    try:
                        detected_faces = self.detector.detect_faces(img_bgr)
                    except Exception as e:
                        logger.error(f"Detection failed for {cur_name}: {e}")
                        failed += 1
                        self.job_repo.update_job_file_status(
                            job_id, file_path, status="failed", error_message=str(e)
                        )
                        continue

                    # Record detected faces & embeddings
                    for face in detected_faces:
                        # Extract embedding if not already set
                        emb = self.embedder.compute_embedding(img_bgr, face)
                        face.embedding = emb

                        # Generate thumbnail
                        thumb_path = self.thumbnail_cache.create_face_thumbnail(
                            img_bgr, list(face.bbox)
                        )
                        face.thumbnail_path = thumb_path

                        self.image_repo.add_detected_face(
                            image_id=image_id,
                            bbox=list(face.bbox),
                            det_score=face.score,
                            embedding=emb,
                            landmarks=face.landmarks.tolist() if face.landmarks is not None else None,
                            thumbnail_path=thumb_path,
                        )

                    self.image_repo.mark_image_processed(
                        image_id=image_id,
                        face_count=len(detected_faces),
                        status="processed",
                    )
                    self.job_repo.update_job_file_status(
                        job_id, file_path, status="completed", image_id=image_id
                    )

                    total_faces += len(detected_faces)
                    processed += 1

                    # Speed and ETA calculations
                    elapsed = time.time() - start_time
                    speed = (processed - job.processed_files) / max(elapsed, 0.001)
                    remaining = (total_files - processed) / max(speed, 0.001) if speed > 0 else 0.0

                    if progress_callback:
                        progress_callback(
                            PipelineProgress(
                                phase="detection",
                                current_file=cur_name,
                                processed_files=processed,
                                total_files=total_files,
                                faces_detected=total_faces,
                                known_matches=0,
                                unknown_clusters=0,
                                no_face_count=0,
                                failed_files=failed,
                                speed=speed,
                                elapsed_seconds=elapsed,
                                remaining_seconds=remaining,
                            )
                        )

                # Commit batch progress to database
                self.job_repo.update_job_progress(
                    job_id=job_id,
                    processed_files=processed,
                    failed_files=failed,
                    faces_detected=total_faces,
                    copied_files=0,
                )

            # 3. Matching Phase: Match faces to known enrolled people
            logger.info(f"Matching faces for Job #{job_id} against enrolled profiles...")
            known_people_dict = self.person_repo.get_all_reference_embeddings()
            all_people = {p.id: p.display_name for p in self.person_repo.list_people()}

            conn = self.image_repo.db.get_connection()
            cur = conn.cursor()
            cur.execute(
                """
                SELECT f.id, fe.embedding_blob
                FROM image_faces f
                JOIN face_embeddings fe ON f.id = fe.face_id
                JOIN images img ON f.image_id = img.id
                JOIN job_files jf ON img.id = jf.image_id
                WHERE jf.job_id = ?
                """,
                (job_id,),
            )

            known_matches_count = 0
            unmatched_faces: List[Tuple[int, np.ndarray]] = []

            for row in cur.fetchall():
                face_id = row["id"]
                emb = np.frombuffer(row["embedding_blob"], dtype=np.float32)
                matched_id, score = self.matcher.find_best_match(emb, known_people_dict)
                if matched_id is not None:
                    self.image_repo.assign_face_person(face_id, matched_id, confidence=score)
                    known_matches_count += 1
                else:
                    unmatched_faces.append((face_id, emb))

            # 4. Clustering Phase: Group unknown recurring faces
            logger.info(f"Clustering {len(unmatched_faces)} unknown faces for Job #{job_id}...")
            clusters = self.clusterer.cluster_faces(unmatched_faces)
            for c in clusters:
                for f_id in c.face_ids:
                    self.image_repo.assign_face_cluster(f_id, c.cluster_id)

            # 5. Organization Planning Phase
            logger.info(f"Generating organization destinations for Job #{job_id} (Mode: {job.mode})...")
            cur.execute(
                """
                SELECT DISTINCT img.id as image_id, img.file_path, img.face_count
                FROM images img
                JOIN job_files jf ON img.id = jf.image_id
                WHERE jf.job_id = ? AND jf.status = 'completed'
                """,
                (job_id,),
            )
            scanned_images = cur.fetchall()

            # Target IDs for separation mode
            import json
            filter_target_ids: Set[int] = set()
            if job.filter_target_ids_json:
                try:
                    filter_target_ids = set(json.loads(job.filter_target_ids_json))
                except Exception:
                    pass

            for img_row in scanned_images:
                img_id = img_row["image_id"]
                faces_records = self.image_repo.get_faces_for_image(img_id)
                detected_faces_list = [
                    DetectedFace(
                        bbox=(f.bbox[0], f.bbox[1], f.bbox[2], f.bbox[3]),
                        score=f.det_score,
                        assigned_person_id=f.assigned_person_id,
                        assigned_cluster_id=f.assigned_cluster_id,
                    )
                    for f in faces_records
                ]

                if job.mode == "separation":
                    # Mode B: Separation / Filter
                    destinations, is_matched = OrganizationRuleEngine.plan_separation(
                        faces=detected_faces_list,
                        target_person_ids=filter_target_ids,
                        known_people_map=all_people,
                        exclusive=True,
                    )
                    if is_matched:
                        for dest in destinations:
                            self.job_repo.record_classification_result(
                                job_id=job_id,
                                image_id=img_id,
                                target_category=dest.category_name,
                                destination_path=dest.relative_folder,
                            )
                else:
                    # Mode A: Categorization
                    destinations = OrganizationRuleEngine.plan_categorization(
                        faces=detected_faces_list,
                        known_people_map=all_people,
                        auto_create_unknown=True,
                    )
                    for dest in destinations:
                        self.job_repo.record_classification_result(
                            job_id=job_id,
                            image_id=img_id,
                            target_category=dest.category_name,
                            destination_path=dest.relative_folder,
                        )

            elapsed = time.time() - start_time
            if progress_callback:
                progress_callback(
                    PipelineProgress(
                        phase="completed",
                        current_file="Completed",
                        processed_files=processed,
                        total_files=total_files,
                        faces_detected=total_faces,
                        known_matches=known_matches_count,
                        unknown_clusters=len(clusters),
                        no_face_count=len(scanned_images) - total_faces,
                        failed_files=failed,
                        speed=processed / max(elapsed, 0.001),
                        elapsed_seconds=elapsed,
                        remaining_seconds=0.0,
                    )
                )

            logger.info(f"Pipeline successfully finished for Job #{job_id}.")
            return True

        except Exception as e:
            logger.error(f"Pipeline crashed for Job #{job_id}: {e}")
            self.job_repo.update_job_status(job_id, "failed")
            raise
