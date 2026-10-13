"""
Mode C: Single & Group Photo Separator view.
Automatically sorts photo collections into Single Photos (1 face), Group Photos (2+ faces), and optional No Face.
"""

from __future__ import annotations
import os
import json
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QFrame, QMessageBox, QSpinBox, QScrollArea
)
from PySide6.QtCore import Qt, Signal, QObject

from facesoter.ui.widgets.progress_panel import ProgressPanel
from facesoter.ui.dialogs.single_group_review_dialog import SingleGroupReviewDialog
from facesoter.core.jobs.job_manager import JobManager
from facesoter.core.jobs.pipeline import PipelineProgress
from facesoter.core.organizer.engine import OrganizerEngine
from facesoter.core.database.repositories.job_repo import JobRepository
from facesoter.core.database.repositories.image_repo import ImageRepository
from facesoter.core.database.repositories.person_repo import PersonRepository
from facesoter.core.settings.config import AppConfig


class SingleGroupSignalBridge(QObject):
    progress = Signal(object)
    scan_finished = Signal(int, bool)
    copy_progress = Signal(int, int, str)
    copy_finished = Signal(int, int, int)


class SingleGroupView(QWidget):
    """View implementing Mode C: Single & Group Photo Separator workflow."""

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

        self.bridge = SingleGroupSignalBridge()
        self.bridge.progress.connect(self._on_pipeline_progress)
        self.bridge.scan_finished.connect(self._on_scan_finished)
        self.bridge.copy_progress.connect(self._on_copy_progress)
        self.bridge.copy_finished.connect(self._on_copy_finished)

        self._current_job_id: int | None = None
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        header = QLabel("Single & Group Photo Separator")
        header.setProperty("class", "page_header")
        main_layout.addWidget(header)

        desc = QLabel(
            "Scans your photo collection, identifies face counts per photo, and organizes images into "
            "Single Photos (solo portraits) and Group Photos (couples, family, events) with 100% on-device AI."
        )
        desc.setWordWrap(True)
        desc.setProperty("class", "page_subheader")
        main_layout.addWidget(desc)

        # Scrollable Configuration Container
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        container = QWidget()
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(16)
        c_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Directory Input Card
        input_card = QFrame()
        input_card.setProperty("class", "card")
        ic_layout = QVBoxLayout(input_card)
        ic_layout.setSpacing(12)

        dir_title = QLabel("1. Folder Selection")
        dir_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        ic_layout.addWidget(dir_title)

        # Source folder
        s_lbl = QLabel("Source Photo Folder:")
        s_lbl.setStyleSheet("font-weight: 600; color: #e4e4e7;")
        ic_layout.addWidget(s_lbl)

        s_box = QHBoxLayout()
        self.source_input = QLineEdit(self.config.default_source_dir)
        self.source_input.setPlaceholderText("Select folder containing photos to separate...")
        s_btn = QPushButton("Browse...")
        s_btn.clicked.connect(self._browse_source)
        s_box.addWidget(self.source_input)
        s_box.addWidget(s_btn)
        ic_layout.addLayout(s_box)

        # Export folder
        e_lbl = QLabel("Destination Export Folder:")
        e_lbl.setStyleSheet("font-weight: 600; color: #e4e4e7;")
        ic_layout.addWidget(e_lbl)

        e_box = QHBoxLayout()
        self.export_input = QLineEdit(self.config.default_export_dir)
        self.export_input.setPlaceholderText("Select destination folder for organized photos...")
        e_btn = QPushButton("Browse...")
        e_btn.clicked.connect(self._browse_export)
        e_box.addWidget(self.export_input)
        e_box.addWidget(e_btn)
        ic_layout.addLayout(e_box)

        self.subfolders_check = QCheckBox("Include subfolders (recursive scan)")
        self.subfolders_check.setChecked(self.config.include_subfolders)
        ic_layout.addWidget(self.subfolders_check)

        c_layout.addWidget(input_card)

        # 2. Separation Options Card
        opts_card = QFrame()
        opts_card.setProperty("class", "card")
        oc_layout = QVBoxLayout(opts_card)
        oc_layout.setSpacing(12)

        opts_title = QLabel("2. Separation & Destination Rules")
        opts_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        oc_layout.addWidget(opts_title)

        # Folder names
        fn_row = QHBoxLayout()
        fn_row.setSpacing(16)

        # Single folder name
        single_box = QVBoxLayout()
        single_lbl = QLabel("Single Photos Subfolder:")
        single_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.single_folder_input = QLineEdit("Single_Photos")
        single_box.addWidget(single_lbl)
        single_box.addWidget(self.single_folder_input)
        fn_row.addLayout(single_box)

        # Group folder name
        group_box = QVBoxLayout()
        group_lbl = QLabel("Group Photos Subfolder:")
        group_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.group_folder_input = QLineEdit("Group_Photos")
        group_box.addWidget(group_lbl)
        group_box.addWidget(self.group_folder_input)
        fn_row.addLayout(group_box)

        oc_layout.addLayout(fn_row)

        # Threshold & No-Face options
        t_row = QHBoxLayout()
        t_row.setSpacing(16)

        # Min faces for group
        min_box = QVBoxLayout()
        min_lbl = QLabel("Minimum Faces to Classify as Group:")
        min_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.min_group_spin = QSpinBox()
        self.min_group_spin.setRange(2, 20)
        self.min_group_spin.setValue(2)
        min_box.addWidget(min_lbl)
        min_box.addWidget(self.min_group_spin)
        t_row.addLayout(min_box)

        # No-face folder name
        noface_box = QVBoxLayout()
        noface_lbl = QLabel("No Face Subfolder Name:")
        noface_lbl.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        self.noface_folder_input = QLineEdit("No_Face")
        noface_box.addWidget(noface_lbl)
        noface_box.addWidget(self.noface_folder_input)
        t_row.addLayout(noface_box)

        oc_layout.addLayout(t_row)

        # Checkboxes
        self.include_noface_check = QCheckBox("Route photos without human faces into No Face folder")
        self.include_noface_check.setChecked(True)
        oc_layout.addWidget(self.include_noface_check)

        self.move_files_check = QCheckBox("Move files instead of copying (Default: False — safe copy)")
        self.move_files_check.setChecked(False)
        oc_layout.addWidget(self.move_files_check)

        # Launch Button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        self.start_btn = QPushButton("Start Single & Group Scan 🚀")
        self.start_btn.setProperty("class", "btn_primary")
        self.start_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 24px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        self.start_btn.clicked.connect(self._start_scan)
        btn_box.addWidget(self.start_btn)
        oc_layout.addLayout(btn_box)

        c_layout.addWidget(opts_card)

        # Progress Panel
        self.progress_panel = ProgressPanel()
        self.progress_panel.pause_requested.connect(self._on_pause)
        self.progress_panel.resume_requested.connect(self._on_resume)
        self.progress_panel.cancel_requested.connect(self._on_cancel)
        self.progress_panel.setVisible(False)
        c_layout.addWidget(self.progress_panel)

        # Action Card / Banner
        self.action_card = QFrame()
        self.action_card.setProperty("class", "card")
        self.action_card.setVisible(False)
        ac_layout = QHBoxLayout(self.action_card)

        self.action_label = QLabel("Scan completed! Review results to start separation.")
        self.action_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        ac_layout.addWidget(self.action_label)
        ac_layout.addStretch()

        self.review_btn = QPushButton("Review & Start Organization")
        self.review_btn.setProperty("class", "btn_primary")
        self.review_btn.clicked.connect(self._open_review_dialog)
        ac_layout.addWidget(self.review_btn)

        self.open_dest_btn = QPushButton("Open Export Folder")
        self.open_dest_btn.clicked.connect(self._open_destination)
        self.open_dest_btn.setVisible(False)
        ac_layout.addWidget(self.open_dest_btn)

        c_layout.addWidget(self.action_card)
        c_layout.addStretch()

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

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

        single_f = self.single_folder_input.text().strip() or "Single_Photos"
        group_f = self.group_folder_input.text().strip() or "Group_Photos"
        noface_f = self.noface_folder_input.text().strip() or "No_Face"
        min_count = self.min_group_spin.value()
        inc_noface = self.include_noface_check.isChecked()

        custom_settings = {
            "single_folder": single_f,
            "group_folder": group_f,
            "no_face_folder": noface_f,
            "min_group_count": min_count,
            "include_no_face": inc_noface,
            "move": self.move_files_check.isChecked(),
        }

        self.start_btn.setEnabled(False)
        self.progress_panel.reset()
        self.progress_panel.setVisible(True)
        self.action_card.setVisible(False)
        self.open_dest_btn.setVisible(False)

        job_name = f"Single vs Group — {Path(src).name}"
        job = self.job_manager.start_job(
            name=job_name,
            mode="single_group",
            source_dir=src,
            export_dir=dst,
            include_subfolders=self.subfolders_check.isChecked(),
            settings=custom_settings,
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
            self.action_label.setText("Scan completed successfully! Review breakdown below.")
            self._open_review_dialog()
        else:
            QMessageBox.information(self, "Scan Stopped", "Scan was cancelled or paused.")

    def _open_review_dialog(self) -> None:
        if not self._current_job_id:
            return

        summary = self.organizer_engine.generate_preview(self._current_job_id)
        classifications = self.job_repo.get_classification_results(self._current_job_id)

        single_count = sum(1 for c in classifications if c.target_category == "Single")
        group_count = sum(1 for c in classifications if c.target_category == "Group")
        no_face_count = sum(1 for c in classifications if c.target_category == "No Face")

        dlg = SingleGroupReviewDialog(
            summary=summary,
            single_count=single_count,
            group_count=group_count,
            no_face_count=no_face_count,
            is_move=self.move_files_check.isChecked(),
            parent=self,
        )

        if dlg.exec():
            self._execute_copy()

    def _execute_copy(self) -> None:
        if not self._current_job_id:
            return

        export_dir = Path(self.export_input.text().strip())
        is_move = self.move_files_check.isChecked()
        action_verb = "Moving" if is_move else "Copying"
        self.action_label.setText(f"{action_verb} photos into Single & Group folders...")
        self.review_btn.setEnabled(False)

        def worker():
            copied, skipped, failed = self.organizer_engine.execute_organization(
                job_id=self._current_job_id,
                export_root=export_dir,
                move=is_move,
                progress_callback=lambda cur, tot, name: self.bridge.copy_progress.emit(cur, tot, name),
            )
            self.bridge.copy_finished.emit(copied, skipped, failed)

        threading.Thread(target=worker, daemon=True).start()

    def _on_copy_progress(self, current: int, total: int, filename: str) -> None:
        is_move = self.move_files_check.isChecked()
        action_verb = "Moving" if is_move else "Copying"
        self.action_label.setText(f"{action_verb} {current} / {total}: {filename}")

    def _on_copy_finished(self, copied: int, skipped: int, failed: int) -> None:
        self.review_btn.setEnabled(True)
        is_move = self.move_files_check.isChecked()
        action_past = "moved" if is_move else "copied"
        self.action_label.setText(
            f"Organization complete! {copied} files {action_past}, {skipped} skipped, {failed} failed."
        )
        self.open_dest_btn.setVisible(True)
        if self._current_job_id:
            self.job_repo.update_job_status(self._current_job_id, "completed", completed=True)
        QMessageBox.information(
            self,
            "Complete",
            f"Single & Group photo separation finished!\n\n"
            f"• Successfully {action_past}: {copied}\n"
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
