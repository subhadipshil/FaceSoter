"""
Mode B: Separation / Filter view for isolating target people with strict categorization exclusion.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import List, Set
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QFileDialog, QCheckBox, QFrame, QMessageBox, QListWidget, QListWidgetItem,
    QInputDialog
)
from PySide6.QtCore import Qt, Signal, QObject
from facesoter.ui.widgets.progress_panel import ProgressPanel
from facesoter.ui.dialogs.face_picker_dialog import FacePickerDialog
from facesoter.core.jobs.job_manager import JobManager
from facesoter.core.jobs.pipeline import PipelineProgress
from facesoter.core.organizer.engine import OrganizerEngine
from facesoter.core.database.repositories.job_repo import JobRepository
from facesoter.core.database.repositories.image_repo import ImageRepository
from facesoter.core.database.repositories.person_repo import PersonRepository
from facesoter.core.ai.provider import FaceDetectionProvider, FaceEmbeddingProvider
from facesoter.core.scanner.image_reader import ImageReader
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache
from facesoter.core.settings.config import AppConfig


class SeparationSignalBridge(QObject):
    progress = Signal(object)
    scan_finished = Signal(int, bool)
    copy_progress = Signal(int, int, str)
    copy_finished = Signal(int, int, int)


class SeparationView(QWidget):
    """View implementing Mode B: Separation / Filter workflow."""

    def __init__(
        self,
        job_manager: JobManager,
        organizer_engine: OrganizerEngine,
        job_repo: JobRepository,
        image_repo: ImageRepository,
        person_repo: PersonRepository,
        detector: FaceDetectionProvider,
        embedder: FaceEmbeddingProvider,
        thumbnail_cache: ThumbnailCache,
        config: AppConfig,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.job_manager = job_manager
        self.organizer_engine = organizer_engine
        self.job_repo = job_repo
        self.image_repo = image_repo
        self.person_repo = person_repo
        self.detector = detector
        self.embedder = embedder
        self.thumbnail_cache = thumbnail_cache
        self.config = config

        self.bridge = SeparationSignalBridge()
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
        header = QLabel("Mode B: Separation / Filter")
        header.setProperty("class", "page_header")
        layout.addWidget(header)

        desc = QLabel(
            "Scan source photos for one or more target person profiles. "
            "Matching photos are copied to SeparateFilter/<Target>/ and strictly excluded "
            "from normal categorization folders."
        )
        desc.setWordWrap(True)
        desc.setProperty("class", "page_subheader")
        layout.addWidget(desc)

        # Main Layout: Left Folder Settings, Right Target People Selector
        row_layout = QHBoxLayout()
        row_layout.setSpacing(16)

        # Left Column: Folders & Rules
        left_card = QFrame()
        left_card.setProperty("class", "card")
        lc_layout = QVBoxLayout(left_card)
        lc_layout.setSpacing(12)

        # Source
        s_lbl = QLabel("Source Folder:")
        s_lbl.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        lc_layout.addWidget(s_lbl)
        s_box = QHBoxLayout()
        self.source_input = QLineEdit(self.config.default_source_dir)
        s_btn = QPushButton("Browse...")
        s_btn.clicked.connect(self._browse_source)
        s_box.addWidget(self.source_input)
        s_box.addWidget(s_btn)
        lc_layout.addLayout(s_box)

        # Export
        e_lbl = QLabel("Export Folder:")
        e_lbl.setStyleSheet("font-weight: bold; color: #e0e0e0;")
        lc_layout.addWidget(e_lbl)
        e_box = QHBoxLayout()
        self.export_input = QLineEdit(self.config.default_export_dir)
        e_btn = QPushButton("Browse...")
        e_btn.clicked.connect(self._browse_export)
        e_box.addWidget(self.export_input)
        e_box.addWidget(e_btn)
        lc_layout.addLayout(e_box)

        # Subfolders
        self.subfolders_check = QCheckBox("Include subfolders (recursive scan)")
        self.subfolders_check.setChecked(self.config.include_subfolders)
        lc_layout.addWidget(self.subfolders_check)

        # Rule explanation card
        rule_box = QFrame()
        rule_box.setStyleSheet("background-color: #1e1e24; border: 1px solid #3e3e4a; border-radius: 6px; padding: 10px;")
        rb_layout = QVBoxLayout(rule_box)
        rb_title = QLabel("CRITICAL SEPARATION RULE:")
        rb_title.setStyleSheet("font-weight: bold; color: #0078d4; font-size: 11px;")
        rb_desc = QLabel(
            "If a photo matches ANY selected target person, it is saved into SeparateFilter/<Target>/ "
            "and will NEVER be copied into normal person folders or No Face."
        )
        rb_desc.setStyleSheet("color: #cccccc; font-size: 11px;")
        rb_desc.setWordWrap(True)
        rb_layout.addWidget(rb_title)
        rb_layout.addWidget(rb_desc)
        lc_layout.addWidget(rule_box)

        self.start_btn = QPushButton("Start Separation Scan")
        self.start_btn.setProperty("class", "btn_primary")
        self.start_btn.clicked.connect(self._start_scan)
        lc_layout.addWidget(self.start_btn)

        row_layout.addWidget(left_card, stretch=3)

        # Right Column: Target People Selector
        right_card = QFrame()
        right_card.setProperty("class", "card")
        rc_layout = QVBoxLayout(right_card)
        rc_layout.setSpacing(10)

        rc_title = QLabel("Select Target People to Filter:")
        rc_title.setStyleSheet("font-weight: bold; color: #ffffff;")
        rc_layout.addWidget(rc_title)

        self.people_list = QListWidget()
        self.people_list.setSelectionMode(QListWidget.SelectionMode.NoSelection)
        rc_layout.addWidget(self.people_list)

        import_btn = QPushButton("Import New Reference Photo...")
        import_btn.clicked.connect(self._import_reference_photo)
        rc_layout.addWidget(import_btn)

        row_layout.addWidget(right_card, stretch=2)
        layout.addLayout(row_layout)

        # Progress Panel
        self.progress_panel = ProgressPanel()
        self.progress_panel.pause_requested.connect(self._on_pause)
        self.progress_panel.resume_requested.connect(self._on_resume)
        self.progress_panel.cancel_requested.connect(self._on_cancel)
        self.progress_panel.setVisible(False)
        layout.addWidget(self.progress_panel)

        # Action banner
        self.action_card = QFrame()
        self.action_card.setProperty("class", "card")
        self.action_card.setVisible(False)
        ac_layout = QHBoxLayout(self.action_card)

        self.action_label = QLabel("")
        self.action_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        ac_layout.addWidget(self.action_label)
        ac_layout.addStretch()

        self.open_dest_btn = QPushButton("Open SeparateFilter Folder")
        self.open_dest_btn.clicked.connect(self._open_destination)
        self.open_dest_btn.setVisible(False)
        ac_layout.addWidget(self.open_dest_btn)

        layout.addWidget(self.action_card)
        layout.addStretch()

        self.refresh_people()

    def refresh_people(self) -> None:
        """Populate enrolled target people checkboxes."""
        self.people_list.clear()
        people = self.person_repo.list_people()
        for p in people:
            item = QListWidgetItem(self.people_list)
            cb = QCheckBox(f"{p.display_name} ({p.sample_count} samples)")
            cb.setProperty("person_id", p.id)
            self.people_list.setItemWidget(item, cb)

    def _get_selected_target_ids(self) -> List[int]:
        selected: List[int] = []
        for i in range(self.people_list.count()):
            item = self.people_list.item(i)
            cb = self.people_list.itemWidget(item)
            if isinstance(cb, QCheckBox) and cb.isChecked():
                pid = cb.property("person_id")
                if pid:
                    selected.append(int(pid))
        return selected

    def _browse_source(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Select Source Photo Folder")
        if sel:
            self.source_input.setText(sel)

    def _browse_export(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Select Destination Export Folder")
        if sel:
            self.export_input.setText(sel)

    def _import_reference_photo(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Photo", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if not file_path:
            return

        name, ok = QInputDialog.getText(
            self, "Person Profile", "Enter the name of the person in this photo:"
        )
        if not ok or not name.strip():
            return
        name = name.strip()

        # Load image & run face detection
        img_bgr, w, h, err = ImageReader.load_image_bgr(file_path)
        if img_bgr is None:
            QMessageBox.critical(self, "Image Error", f"Could not load image:\n{err}")
            return

        try:
            detected = self.detector.detect_faces(img_bgr)
        except Exception as e:
            QMessageBox.critical(self, "Inference Error", f"Model detection failed:\n{e}")
            return

        if not detected:
            QMessageBox.warning(
                self, "No Face Detected", "No human face was detected in this reference photo."
            )
            return

        # Handle multiple faces in reference photo
        chosen_face = detected[0]
        if len(detected) > 1:
            for f in detected:
                f.thumbnail_path = self.thumbnail_cache.create_face_thumbnail(img_bgr, list(f.bbox))
            dlg = FacePickerDialog(name, detected, parent=self)
            if dlg.exec() and dlg.selected_face:
                chosen_face = dlg.selected_face
            else:
                return

        # Compute embedding
        emb = self.embedder.compute_embedding(img_bgr, chosen_face)
        thumb = self.thumbnail_cache.create_face_thumbnail(img_bgr, list(chosen_face.bbox))

        # Check if person already exists or create new
        existing_people = self.person_repo.list_people()
        target_person = next((p for p in existing_people if p.display_name.lower() == name.lower()), None)
        if not target_person:
            target_person = self.person_repo.create_person(display_name=name)

        self.person_repo.add_reference_face(
            person_id=target_person.id,
            image_path=file_path,
            bbox=list(chosen_face.bbox),
            embedding=emb,
            landmarks=chosen_face.landmarks.tolist() if chosen_face.landmarks is not None else None,
            thumbnail_path=thumb,
        )

        self.refresh_people()
        # Automatically check this person
        for i in range(self.people_list.count()):
            item = self.people_list.item(i)
            cb = self.people_list.itemWidget(item)
            if isinstance(cb, QCheckBox) and cb.property("person_id") == target_person.id:
                cb.setChecked(True)

        QMessageBox.information(
            self, "Reference Added", f"Added reference sample for '{name}' successfully!"
        )

    def _start_scan(self) -> None:
        src = self.source_input.text().strip()
        dst = self.export_input.text().strip()
        targets = self._get_selected_target_ids()

        if not src or not Path(src).exists():
            QMessageBox.warning(self, "Invalid Path", "Please select a valid source folder.")
            return
        if not dst:
            QMessageBox.warning(self, "Invalid Path", "Please select a destination export folder.")
            return
        if not targets:
            QMessageBox.warning(
                self, "No Targets Selected", "Please select at least one target person to filter."
            )
            return

        self.start_btn.setEnabled(False)
        self.progress_panel.reset()
        self.progress_panel.setVisible(True)
        self.action_card.setVisible(False)

        job_name = f"Separation — {Path(src).name}"
        job = self.job_manager.start_job(
            name=job_name,
            mode="separation",
            source_dir=src,
            export_dir=dst,
            include_subfolders=self.subfolders_check.isChecked(),
            filter_target_ids=targets,
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
            self._execute_copy()
        else:
            QMessageBox.information(self, "Scan Stopped", "Scan was cancelled or paused.")

    def _execute_copy(self) -> None:
        if not self._current_job_id:
            return

        export_dir = Path(self.export_input.text().strip())
        self.action_card.setVisible(True)
        self.action_label.setText("Copying matched photos into SeparateFilter folders...")

        import threading

        def worker():
            copied, skipped, failed = self.organizer_engine.execute_organization(
                job_id=self._current_job_id,
                export_root=export_dir,
                progress_callback=lambda cur, tot, name: self.bridge.copy_progress.emit(cur, tot, name),
            )
            self.bridge.copy_finished.emit(copied, skipped, failed)

        threading.Thread(target=worker, daemon=True).start()

    def _on_copy_progress(self, cur: int, tot: int, name: str) -> None:
        self.action_label.setText(f"Filtering {cur} / {tot}: {name}")

    def _on_copy_finished(self, copied: int, skipped: int, failed: int) -> None:
        self.action_label.setText(
            f"Separation complete! {copied} matching photos separated into SeparateFilter/."
        )
        self.open_dest_btn.setVisible(True)
        if self._current_job_id:
            self.job_repo.update_job_status(self._current_job_id, "completed", completed=True)
        QMessageBox.information(
            self,
            "Separation Finished",
            f"Separation / Filter complete!\n\n"
            f"• Matched Photos Copied: {copied}\n"
            f"• Skipped: {skipped}\n"
            f"• Failed: {failed}",
        )

    def _open_destination(self) -> None:
        dst = self.export_input.text().strip()
        if dst:
            p = Path(dst) / "SeparateFilter"
            p.mkdir(parents=True, exist_ok=True)
            os.startfile(str(p))

    def _handle_error(self, job_id: int, err: str) -> None:
        self.start_btn.setEnabled(True)
        QMessageBox.critical(self, "Job Error", f"Separation scan error:\n\n{err}")
