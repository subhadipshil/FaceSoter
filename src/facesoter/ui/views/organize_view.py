"""
Mode A: Categorization view for organizing photo collections into person folders.
"""

from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QFrame, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QObject
from facesoter.ui.widgets.progress_panel import ProgressPanel
from facesoter.ui.dialogs.review_dialog import ReviewDialog
from facesoter.core.jobs.job_manager import JobManager
from facesoter.core.jobs.pipeline import PipelineProgress
from facesoter.core.organizer.engine import OrganizerEngine
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord
from facesoter.core.database.repositories.image_repo import ImageRepository
from facesoter.core.database.repositories.person_repo import PersonRepository
from facesoter.core.settings.config import AppConfig


class OrganizeSignalBridge(QObject):
    progress = Signal(object)
    scan_finished = Signal(int, bool)
    copy_progress = Signal(int, int, str)
    copy_finished = Signal(int, int, int)


class OrganizeView(QWidget):
    """View implementing Mode A: Categorization workflow."""

    def __init__(
        self,
        job_manager: JobManager,
        organizer_engine: OrganizerEngine,
        job_repo: JobRepository,
        image_repo: ImageRepository,
        person_repo: PersonRepository,
        config: AppConfig,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.job_manager = job_manager
        self.organizer_engine = organizer_engine
        self.job_repo = job_repo
        self.image_repo = image_repo
        self.person_repo = person_repo
        self.config = config

        self.bridge = OrganizeSignalBridge()
        self.bridge.progress.connect(self._on_pipeline_progress)
        self.bridge.scan_finished.connect(self._on_scan_finished)
        self.bridge.copy_progress.connect(self._on_copy_progress)
        self.bridge.copy_finished.connect(self._on_copy_finished)

        self._current_job_id: int | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("Mode A: Photo Categorization")
        header.setProperty("class", "page_header")
        layout.addWidget(header)

        desc = QLabel(
            "Scans photos, identifies human faces, and organizes images into person folders. "
            "Photos with multiple people are duplicated into every relevant folder. "
            "Photos without faces go to Uncategorized/No Face/."
        )
        desc.setWordWrap(True)
        desc.setProperty("class", "page_subheader")
        layout.addWidget(desc)

        # Input Card
        input_card = QFrame()
        input_card.setProperty("class", "card")
        ic_layout = QVBoxLayout(input_card)
        ic_layout.setSpacing(12)

        # Source folder
        s_lbl = QLabel("Source Folder:")
        s_lbl.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        ic_layout.addWidget(s_lbl)

        s_box = QHBoxLayout()
        self.source_input = QLineEdit(self.config.default_source_dir)
        self.source_input.setPlaceholderText("Select directory containing photos to organize...")
        s_btn = QPushButton("Browse...")
        s_btn.clicked.connect(self._browse_source)
        s_box.addWidget(self.source_input)
        s_box.addWidget(s_btn)
        ic_layout.addLayout(s_box)

        # Export folder
        e_lbl = QLabel("Export Folder:")
        e_lbl.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        ic_layout.addWidget(e_lbl)

        e_box = QHBoxLayout()
        self.export_input = QLineEdit(self.config.default_export_dir)
        self.export_input.setPlaceholderText("Select destination directory for organized photos...")
        e_btn = QPushButton("Browse...")
        e_btn.clicked.connect(self._browse_export)
        e_box.addWidget(self.export_input)
        e_box.addWidget(e_btn)
        ic_layout.addLayout(e_box)

        # Options
        opts_box = QHBoxLayout()
        self.subfolders_check = QCheckBox("Include subfolders (recursive scan)")
        self.subfolders_check.setChecked(self.config.include_subfolders)
        opts_box.addWidget(self.subfolders_check)
        opts_box.addStretch()

        self.start_btn = QPushButton("Start Categorization Scan")
        self.start_btn.setProperty("class", "btn_primary")
        self.start_btn.clicked.connect(self._start_scan)
        opts_box.addWidget(self.start_btn)
        ic_layout.addLayout(opts_box)

        layout.addWidget(input_card)

        # Progress Panel
        self.progress_panel = ProgressPanel()
        self.progress_panel.pause_requested.connect(self._on_pause)
        self.progress_panel.resume_requested.connect(self._on_resume)
        self.progress_panel.cancel_requested.connect(self._on_cancel)
        self.progress_panel.setVisible(False)
        layout.addWidget(self.progress_panel)

        # Result / Action Banner
        self.action_card = QFrame()
        self.action_card.setProperty("class", "card")
        self.action_card.setVisible(False)
        ac_layout = QHBoxLayout(self.action_card)

        self.action_label = QLabel("Scan completed! Review results to start copying.")
        self.action_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        ac_layout.addWidget(self.action_label)
        ac_layout.addStretch()

        self.review_btn = QPushButton("Review & Start Copy")
        self.review_btn.setProperty("class", "btn_primary")
        self.review_btn.clicked.connect(self._open_review_dialog)
        ac_layout.addWidget(self.review_btn)

        self.open_dest_btn = QPushButton("Open Export Folder")
        self.open_dest_btn.clicked.connect(self._open_destination)
        self.open_dest_btn.setVisible(False)
        ac_layout.addWidget(self.open_dest_btn)

        layout.addWidget(self.action_card)
        layout.addStretch()

    def _browse_source(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Select Source Photo Folder")
        if sel:
            self.source_input.setText(sel)

    def _browse_export(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Select Destination Export Folder")
        if sel:
            self.export_input.setText(sel)

    def _start_scan(self) -> None:
        src = self.source_input.text().strip()
        dst = self.export_input.text().strip()

        if not src or not Path(src).exists():
            QMessageBox.warning(self, "Invalid Path", "Please select a valid source folder.")
            return
        if not dst:
            QMessageBox.warning(self, "Invalid Path", "Please select a destination export folder.")
            return

        self.start_btn.setEnabled(False)
        self.progress_panel.reset()
        self.progress_panel.setVisible(True)
        self.action_card.setVisible(False)
        self.open_dest_btn.setVisible(False)

        job_name = f"Categorize — {Path(src).name}"
        job = self.job_manager.start_job(
            name=job_name,
            mode="categorization",
            source_dir=src,
            export_dir=dst,
            include_subfolders=self.subfolders_check.isChecked(),
            on_progress=lambda p: self.bridge.progress.emit(p),
            on_finished=lambda jid, ok: self.bridge.scan_finished.emit(jid, ok),
            on_error=lambda jid, err: self._handle_error(jid, err),
        )
        self._current_job_id = job.id

    def _on_pause(self) -> None:
        if self._current_job_id:
            self.job_manager.pause_job(self._current_job_id)

    def _on_resume(self) -> None:
        if self._current_job_id:
            self.job_manager.resume_job(
                self._current_job_id,
                on_progress=lambda p: self.bridge.progress.emit(p),
                on_finished=lambda jid, ok: self.bridge.scan_finished.emit(jid, ok),
                on_error=lambda jid, err: self._handle_error(jid, err),
            )

    def _on_cancel(self) -> None:
        if self._current_job_id:
            self.job_manager.cancel_job(self._current_job_id)
        self.start_btn.setEnabled(True)

    def _on_pipeline_progress(self, p: PipelineProgress) -> None:
        self.progress_panel.update_progress(p)

    def _on_scan_finished(self, job_id: int, success: bool) -> None:
        self.start_btn.setEnabled(True)
        if success:
            self.action_card.setVisible(True)
            self.action_label.setText("Scan completed successfully! Review detected clusters below.")
            self._open_review_dialog()
        else:
            QMessageBox.information(self, "Scan Stopped", "Scan was cancelled or paused.")

    def _open_review_dialog(self) -> None:
        if not self._current_job_id:
            return

        summary = self.organizer_engine.generate_preview(self._current_job_id)

        # Collect detected cluster thumbnails
        conn = self.image_repo.db.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT f.assigned_cluster_id, f.thumbnail_path, COUNT(f.id) as sample_count
            FROM image_faces f
            JOIN images img ON f.image_id = img.id
            JOIN job_files jf ON img.id = jf.image_id
            WHERE jf.job_id = ? AND f.assigned_cluster_id IS NOT NULL
            GROUP BY f.assigned_cluster_id
            ORDER BY sample_count DESC
            """,
            (self._current_job_id,),
        )
        cluster_items = [
            {
                "id": r["assigned_cluster_id"],
                "name": r["assigned_cluster_id"],
                "count": r["sample_count"],
                "thumb_path": r["thumbnail_path"],
            }
            for r in cur.fetchall()
        ]

        dlg = ReviewDialog(summary=summary, cluster_items=cluster_items, parent=self)
        dlg.rename_requested.connect(self._rename_cluster)

        if dlg.exec():
            # User confirmed [Start Organization]
            self._execute_copy()

    def _rename_cluster(self, old_name: str, new_name: str) -> None:
        if not self._current_job_id:
            return
        with self.image_repo.db.transaction() as cur:
            # Update image_faces assigned_cluster_id
            cur.execute(
                "UPDATE image_faces SET assigned_cluster_id = ? WHERE assigned_cluster_id = ?",
                (new_name, old_name),
            )
            # Update classification_results target_category and destination_path
            old_rel = f"Categorized/{old_name}"
            new_rel = f"Categorized/{new_name}"
            cur.execute(
                """
                UPDATE classification_results
                SET target_category = ?, destination_path = ?
                WHERE job_id = ? AND target_category = ?
                """,
                (new_name, new_rel, self._current_job_id, old_name),
            )

    def _execute_copy(self) -> None:
        if not self._current_job_id:
            return

        export_dir = Path(self.export_input.text().strip())
        self.action_label.setText("Copying files to categorized destinations...")
        self.review_btn.setEnabled(False)

        import threading

        def worker():
            copied, skipped, failed = self.organizer_engine.execute_organization(
                job_id=self._current_job_id,
                export_root=export_dir,
                progress_callback=lambda cur, tot, name: self.bridge.copy_progress.emit(cur, tot, name),
            )
            self.bridge.copy_finished.emit(copied, skipped, failed)

        threading.Thread(target=worker, daemon=True).start()

    def _on_copy_progress(self, current: int, total: int, filename: str) -> None:
        self.action_label.setText(f"Copying {current} / {total}: {filename}")

    def _on_copy_finished(self, copied: int, skipped: int, failed: int) -> None:
        self.review_btn.setEnabled(True)
        self.action_label.setText(
            f"Organization complete! {copied} files copied, {skipped} skipped, {failed} failed."
        )
        self.open_dest_btn.setVisible(True)
        if self._current_job_id:
            self.job_repo.update_job_status(self._current_job_id, "completed", completed=True)
        QMessageBox.information(
            self,
            "Complete",
            f"Photo organization finished!\n\n"
            f"• Copied: {copied}\n"
            f"• Skipped: {skipped}\n"
            f"• Failed: {failed}",
        )

    def _open_destination(self) -> None:
        p = self.export_input.text().strip()
        if p and Path(p).exists():
            os.startfile(p)

    def _handle_error(self, job_id: int, error_msg: str) -> None:
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Job Error", f"An error occurred during scanning:\n\n{error_msg}")
