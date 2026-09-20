"""
Job lifecycle manager coordinating background workers and recovery.
"""

from __future__ import annotations
from typing import Dict, Optional, Callable, List, Any
from facesoter.core.jobs.worker import JobWorker
from facesoter.core.jobs.pipeline import ScanPipeline, PipelineProgress
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord
from facesoter.core.logging.logger import get_logger

logger = get_logger("job_manager")


class JobManager:
    """Manages creation, execution, pause, resume, and cancellation of scanning jobs."""

    def __init__(self, job_repo: JobRepository, pipeline_factory: Callable[[], ScanPipeline]):
        self.job_repo = job_repo
        self.pipeline_factory = pipeline_factory
        self._active_workers: Dict[int, JobWorker] = {}

    def start_job(
        self,
        name: str,
        mode: str,
        source_dir: str,
        export_dir: str,
        include_subfolders: bool = True,
        settings_dict: Optional[Dict[str, Any]] = None,
        filter_target_ids: Optional[List[int]] = None,
        on_progress: Optional[Callable[[PipelineProgress], None]] = None,
        on_finished: Optional[Callable[[int, bool], None]] = None,
        on_error: Optional[Callable[[int, str], None]] = None,
    ) -> JobRecord:
        """Create and start a new scan job."""
        job = self.job_repo.create_job(
            name=name,
            mode=mode,
            source_dir=source_dir,
            export_dir=export_dir,
            include_subfolders=include_subfolders,
            settings_dict=settings_dict,
            filter_target_ids=filter_target_ids,
        )

        pipeline = self.pipeline_factory()
        worker = JobWorker(
            pipeline=pipeline,
            job_id=job.id,
            on_progress=on_progress,
            on_finished=lambda jid, ok: self._handle_job_finished(jid, ok, on_finished),
            on_error=lambda jid, err: self._handle_job_error(jid, err, on_error),
        )

        self._active_workers[job.id] = worker
        worker.start()
        return job

    def resume_job(
        self,
        job_id: int,
        on_progress: Optional[Callable[[PipelineProgress], None]] = None,
        on_finished: Optional[Callable[[int, bool], None]] = None,
        on_error: Optional[Callable[[int, str], None]] = None,
    ) -> bool:
        """Resume a paused or interrupted job from its database checkpoint."""
        job = self.job_repo.get_job(job_id)
        if not job:
            return False

        if job_id in self._active_workers and self._active_workers[job_id].is_alive():
            logger.warning(f"Job #{job_id} is already running.")
            return True

        pipeline = self.pipeline_factory()
        worker = JobWorker(
            pipeline=pipeline,
            job_id=job_id,
            on_progress=on_progress,
            on_finished=lambda jid, ok: self._handle_job_finished(jid, ok, on_finished),
            on_error=lambda jid, err: self._handle_job_error(jid, err, on_error),
        )

        self._active_workers[job_id] = worker
        worker.start()
        return True

    def pause_job(self, job_id: int) -> bool:
        """Pause a running job."""
        if job_id in self._active_workers:
            self._active_workers[job_id].pause()
            return True
        return False

    def cancel_job(self, job_id: int) -> bool:
        """Cancel a running job."""
        if job_id in self._active_workers:
            self._active_workers[job_id].cancel()
            return True
        self.job_repo.update_job_status(job_id, "cancelled")
        return True

    def _handle_job_finished(
        self, job_id: int, success: bool, callback: Optional[Callable[[int, bool], None]]
    ) -> None:
        if job_id in self._active_workers:
            del self._active_workers[job_id]
        if callback:
            callback(job_id, success)

    def _handle_job_error(
        self, job_id: int, error_msg: str, callback: Optional[Callable[[int, str], None]]
    ) -> None:
        if job_id in self._active_workers:
            del self._active_workers[job_id]
        if callback:
            callback(job_id, error_msg)
