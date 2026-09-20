"""
Background worker thread with pause, resume, and cancellation support.
"""

from __future__ import annotations
import threading
from typing import Optional, Callable
from facesoter.core.jobs.pipeline import ScanPipeline, PipelineProgress
from facesoter.core.logging.logger import get_logger

logger = get_logger("job_worker")


class JobWorker(threading.Thread):
    """Background worker executing the scan pipeline with cooperative pause/cancel."""

    def __init__(
        self,
        pipeline: ScanPipeline,
        job_id: int,
        batch_size: int = 32,
        on_progress: Optional[Callable[[PipelineProgress], None]] = None,
        on_finished: Optional[Callable[[int, bool], None]] = None,
        on_error: Optional[Callable[[int, str], None]] = None,
    ):
        super().__init__(daemon=True, name=f"JobWorker-{job_id}")
        self.pipeline = pipeline
        self.job_id = job_id
        self.batch_size = batch_size
        self.on_progress = on_progress
        self.on_finished = on_finished
        self.on_error = on_error

        self._pause_event = threading.Event()
        self._cancel_event = threading.Event()

    def pause(self) -> None:
        """Pause worker execution at the next file boundary."""
        logger.info(f"Pause requested for Job #{self.job_id}")
        self._pause_event.set()

    def resume(self) -> None:
        """Resume paused worker."""
        logger.info(f"Resume requested for Job #{self.job_id}")
        self._pause_event.clear()

    def cancel(self) -> None:
        """Cancel worker execution."""
        logger.info(f"Cancel requested for Job #{self.job_id}")
        self._cancel_event.set()

    def is_paused(self) -> bool:
        return self._pause_event.is_set()

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()

    def run(self) -> None:
        """Run worker loop."""
        try:
            logger.info(f"Worker started for Job #{self.job_id}")
            success = self.pipeline.run_pipeline(
                job_id=self.job_id,
                batch_size=self.batch_size,
                progress_callback=self.on_progress,
                cancel_check=self.is_cancelled,
                pause_check=self.is_paused,
            )
            if self.on_finished:
                self.on_finished(self.job_id, success)
        except Exception as e:
            logger.error(f"Worker encountered unhandled error on Job #{self.job_id}: {e}")
            if self.on_error:
                self.on_error(self.job_id, str(e))
