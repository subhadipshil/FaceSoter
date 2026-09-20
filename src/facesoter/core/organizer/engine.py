"""
Execution engine for generating pre-copy previews and executing file organization.
"""

from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Callable
from dataclasses import dataclass
from facesoter.core.organizer.rule_engine import OrganizationRuleEngine, PlannedDestination
from facesoter.core.organizer.file_copier import SafeFileCopier
from facesoter.core.database.repositories.job_repo import JobRepository, ClassificationRecord
from facesoter.core.database.repositories.image_repo import ImageRepository
from facesoter.core.logging.logger import get_logger

logger = get_logger("organizer_engine")


@dataclass
class PreCopySummary:
    photos_scanned: int
    photos_with_faces: int
    photos_without_faces: int
    people_detected: int
    known_people_count: int
    unknown_clusters_count: int
    total_copies_to_perform: int
    destination_tree: Dict[str, int]  # relative folder -> file count


class OrganizerEngine:
    """Manages pre-copy preview generation and safe file organization execution."""

    def __init__(
        self,
        job_repo: JobRepository,
        image_repo: ImageRepository,
        file_copier: Optional[SafeFileCopier] = None,
    ):
        self.job_repo = job_repo
        self.image_repo = image_repo
        self.file_copier = file_copier or SafeFileCopier()

    def generate_preview(self, job_id: int) -> PreCopySummary:
        """
        Generate statistical breakdown and destination tree preview for a scanned job
        prior to executing any disk copy operations.
        """
        classifications = self.job_repo.get_classification_results(job_id)
        job = self.job_repo.get_job(job_id)

        tree: Dict[str, int] = {}
        for c in classifications:
            # target folder relative to export_dir
            rel = c.destination_path
            tree[rel] = tree.get(rel, 0) + 1

        total_scanned = job.total_files if job else len(classifications)
        no_face_count = tree.get("Uncategorized/No Face", 0)
        with_faces_count = total_scanned - no_face_count

        known_people = set()
        unknown_clusters = set()

        for c in classifications:
            cat = c.target_category
            if cat not in ("No Face", "Unknown"):
                if cat.startswith("Person "):
                    unknown_clusters.add(cat)
                else:
                    known_people.add(cat)

        return PreCopySummary(
            photos_scanned=total_scanned,
            photos_with_faces=max(0, with_faces_count),
            photos_without_faces=no_face_count,
            people_detected=len(known_people) + len(unknown_clusters),
            known_people_count=len(known_people),
            unknown_clusters_count=len(unknown_clusters),
            total_copies_to_perform=len(classifications),
            destination_tree=tree,
        )

    def execute_organization(
        self,
        job_id: int,
        export_root: Path,
        move: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> Tuple[int, int, int]:
        """
        Perform actual safe atomic copying of files into categorized destinations.
        Returns: (copied_count, skipped_count, failed_count)
        """
        classifications = self.job_repo.get_classification_results(job_id)
        total = len(classifications)
        copied = 0
        skipped = 0
        failed = 0

        logger.info(f"Starting organization copy for Job #{job_id}: {total} operations planned.")

        for i, record in enumerate(classifications):
            if cancel_check and cancel_check():
                logger.info("Organization execution cancelled by user.")
                break

            # Fetch source file path
            conn = self.image_repo.db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT file_path FROM images WHERE id = ?", (record.image_id,))
            row = cur.fetchone()
            if not row:
                failed += 1
                self.job_repo.update_classification_copy_status(
                    record.id, "failed", "Image record not found in database"
                )
                continue

            source_path = Path(row["file_path"])
            dest_dir = export_root / record.destination_path

            success, final_path, err = self.file_copier.copy_file_atomic(
                source_path=source_path,
                destination_dir=dest_dir,
                move=move,
            )

            if success:
                if err and "Skipped" in err:
                    skipped += 1
                    status = "skipped"
                else:
                    copied += 1
                    status = "copied"
                self.job_repo.update_classification_copy_status(record.id, status, err)
            else:
                failed += 1
                self.job_repo.update_classification_copy_status(record.id, "failed", err)

            # Update job live progress
            self.job_repo.update_job_progress(
                job_id=job_id,
                processed_files=total,
                failed_files=failed,
                faces_detected=0,
                copied_files=copied,
            )

            if progress_callback:
                progress_callback(i + 1, total, source_path.name)

        logger.info(
            f"Organization copy completed for Job #{job_id}: {copied} copied, {skipped} skipped, {failed} failed."
        )
        return copied, skipped, failed
