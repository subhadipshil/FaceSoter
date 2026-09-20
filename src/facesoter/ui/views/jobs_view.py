"""
Jobs history and crash recovery view.
"""

from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox
)
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord
from facesoter.core.jobs.job_manager import JobManager
from facesoter.ui.dialogs.failed_files_dialog import FailedFilesDialog


class JobsView(QWidget):
    """View displaying job history and checkpoint resumption."""

    def __init__(
        self,
        job_repo: JobRepository,
        job_manager: JobManager,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.job_repo = job_repo
        self.job_manager = job_manager
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        header = QLabel("Job History & Recovery")
        header.setProperty("class", "page_header")
        layout.addWidget(header)

        desc = QLabel(
            "Inspect past scanning and organization jobs. "
            "Interrupted or paused jobs can be resumed from their last saved checkpoint."
        )
        desc.setProperty("class", "page_subheader")
        layout.addWidget(desc)

        # Table
        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Name", "Mode", "Status", "Photos", "Faces", "Copied", "Date"]
        )
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        for col in [0, 2, 3, 4, 5, 6, 7]:
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

        # Action Buttons
        btn_layout = QHBoxLayout()
        self.resume_btn = QPushButton("Resume Selected Job")
        self.resume_btn.setProperty("class", "btn_primary")
        self.resume_btn.clicked.connect(self._resume_selected)
        btn_layout.addWidget(self.resume_btn)

        self.failed_btn = QPushButton("View Failed Files...")
        self.failed_btn.clicked.connect(self._view_failed)
        btn_layout.addWidget(self.failed_btn)

        self.open_src_btn = QPushButton("Open Source Folder")
        self.open_src_btn.clicked.connect(self._open_source)
        btn_layout.addWidget(self.open_src_btn)

        self.open_exp_btn = QPushButton("Open Export Folder")
        self.open_exp_btn.clicked.connect(self._open_export)
        btn_layout.addWidget(self.open_exp_btn)

        btn_layout.addStretch()

        refresh_btn = QPushButton("Refresh")
        refresh_btn.clicked.connect(self.refresh)
        btn_layout.addWidget(refresh_btn)

        layout.addLayout(btn_layout)
        self.refresh()

    def refresh(self) -> None:
        jobs = self.job_repo.list_jobs(limit=100)
        self.table.setRowCount(len(jobs))
        for row, j in enumerate(jobs):
            id_item = QTableWidgetItem(str(j.id))
            id_item.setData(1000, j.id)
            self.table.setItem(row, 0, id_item)
            self.table.setItem(row, 1, QTableWidgetItem(j.name))
            self.table.setItem(row, 2, QTableWidgetItem(j.mode.capitalize()))
            self.table.setItem(row, 3, QTableWidgetItem(j.status.capitalize()))
            self.table.setItem(row, 4, QTableWidgetItem(f"{j.processed_files} / {j.total_files}"))
            self.table.setItem(row, 5, QTableWidgetItem(str(j.faces_detected)))
            self.table.setItem(row, 6, QTableWidgetItem(str(j.copied_files)))
            date_str = j.created_at[:16].replace("T", " ") if len(j.created_at) >= 16 else j.created_at
            self.table.setItem(row, 7, QTableWidgetItem(date_str))

    def _get_selected_job_id(self) -> int | None:
        cur_row = self.table.currentRow()
        if cur_row < 0:
            return None
        item = self.table.item(cur_row, 0)
        return item.data(1000) if item else None

    def _resume_selected(self) -> None:
        jid = self._get_selected_job_id()
        if not jid:
            QMessageBox.information(self, "Select Job", "Please select a job to resume.")
            return

        job = self.job_repo.get_job(jid)
        if not job:
            return

        if job.status not in ("paused", "interrupted", "failed"):
            QMessageBox.warning(
                self, "Cannot Resume", f"Job #{jid} has status '{job.status}' and cannot be resumed."
            )
            return

        ok = self.job_manager.resume_job(jid)
        if ok:
            QMessageBox.information(self, "Resuming", f"Job #{jid} resumed in the background.")
            self.refresh()

    def _view_failed(self) -> None:
        jid = self._get_selected_job_id()
        if not jid:
            QMessageBox.information(self, "Select Job", "Please select a job first.")
            return

        failed = self.job_repo.get_failed_files(jid)
        if not failed:
            QMessageBox.information(self, "No Failed Files", f"Job #{jid} had 0 failed files.")
            return

        dlg = FailedFilesDialog(failed, parent=self)
        dlg.exec()

    def _open_source(self) -> None:
        jid = self._get_selected_job_id()
        if not jid:
            return
        job = self.job_repo.get_job(jid)
        if job and Path(job.source_dir).exists():
            os.startfile(job.source_dir)

    def _open_export(self) -> None:
        jid = self._get_selected_job_id()
        if not jid:
            return
        job = self.job_repo.get_job(jid)
        if job and Path(job.export_dir).exists():
            os.startfile(job.export_dir)
