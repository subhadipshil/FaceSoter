"""
People view for managing enrolled person profiles and reference face samples.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget,
    QListWidgetItem, QFrame, QSplitter, QFileDialog, QMessageBox, QInputDialog,
    QScrollArea, QGridLayout
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from facesoter.core.database.repositories.person_repo import PersonRepository, Person, ReferenceFace
from facesoter.core.ai.provider import FaceDetectionProvider, FaceEmbeddingProvider
from facesoter.core.scanner.image_reader import ImageReader
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache
from facesoter.ui.dialogs.face_picker_dialog import FacePickerDialog


class PeopleView(QWidget):
    """View for Person profiles database management."""

    def __init__(
        self,
        person_repo: PersonRepository,
        detector: FaceDetectionProvider,
        embedder: FaceEmbeddingProvider,
        thumbnail_cache: ThumbnailCache,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.person_repo = person_repo
        self.detector = detector
        self.embedder = embedder
        self.thumbnail_cache = thumbnail_cache

        self._current_person: Optional[Person] = None
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Header
        header = QLabel("People & Profiles")
        header.setProperty("class", "page_header")
        layout.addWidget(header)

        desc = QLabel(
            "Manage known people and reference face photos. "
            "Enrolled profiles are used across both Categorization and Separation modes."
        )
        desc.setProperty("class", "page_subheader")
        layout.addWidget(desc)

        # Splitter: Left List, Right Profile Details
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Column: Enrolled People List
        left_widget = QWidget()
        lw_layout = QVBoxLayout(left_widget)
        lw_layout.setContentsMargins(0, 0, 0, 0)
        lw_layout.setSpacing(10)

        lw_title = QLabel("Enrolled People")
        lw_title.setStyleSheet("font-weight: bold; color: #ffffff;")
        lw_layout.addWidget(lw_title)

        self.people_list = QListWidget()
        self.people_list.currentRowChanged.connect(self._on_person_selected)
        lw_layout.addWidget(self.people_list)

        # Buttons under list
        btn_box = QHBoxLayout()
        add_btn = QPushButton("Add Person")
        add_btn.setProperty("class", "btn_primary")
        add_btn.clicked.connect(self._add_person)
        btn_box.addWidget(add_btn)

        del_btn = QPushButton("Delete")
        del_btn.setProperty("class", "btn_danger")
        del_btn.clicked.connect(self._delete_person)
        btn_box.addWidget(del_btn)
        lw_layout.addLayout(btn_box)

        merge_btn = QPushButton("Merge with Another...")
        merge_btn.clicked.connect(self._merge_person)
        lw_layout.addWidget(merge_btn)

        splitter.addWidget(left_widget)

        # Right Column: Profile Details & Samples Gallery
        right_frame = QFrame()
        right_frame.setProperty("class", "card")
        self.rf_layout = QVBoxLayout(right_frame)
        self.rf_layout.setSpacing(12)

        self.name_label = QLabel("Select a person from the list")
        self.name_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        self.rf_layout.addWidget(self.name_label)

        self.meta_label = QLabel("")
        self.meta_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.rf_layout.addWidget(self.meta_label)

        # Gallery
        gallery_title = QLabel("Reference Face Samples:")
        gallery_title.setStyleSheet("font-weight: bold; color: #cccccc;")
        self.rf_layout.addWidget(gallery_title)

        self.gallery_scroll = QScrollArea()
        self.gallery_scroll.setWidgetResizable(True)
        self.gallery_container = QWidget()
        self.gallery_grid = QGridLayout(self.gallery_container)
        self.gallery_grid.setSpacing(10)
        self.gallery_scroll.setWidget(self.gallery_container)
        self.rf_layout.addWidget(self.gallery_scroll)

        # Gallery actions
        g_btn_layout = QHBoxLayout()
        self.add_photo_btn = QPushButton("Add Reference Photo...")
        self.add_photo_btn.setProperty("class", "btn_primary")
        self.add_photo_btn.clicked.connect(self._add_reference_photo)
        self.add_photo_btn.setEnabled(False)
        g_btn_layout.addWidget(self.add_photo_btn)

        self.rename_btn = QPushButton("Rename Person...")
        self.rename_btn.clicked.connect(self._rename_person)
        self.rename_btn.setEnabled(False)
        g_btn_layout.addWidget(self.rename_btn)
        g_btn_layout.addStretch()

        self.rf_layout.addLayout(g_btn_layout)

        splitter.addWidget(right_frame)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        self.refresh()

    def refresh(self) -> None:
        """Reload people list."""
        self.people_list.clear()
        people = self.person_repo.list_people()
        for p in people:
            item = QListWidgetItem(f"{p.display_name} ({p.sample_count} samples)")
            item.setData(Qt.ItemDataRole.UserRole, p.id)
            self.people_list.addItem(item)

        if self.people_list.count() > 0:
            self.people_list.setCurrentRow(0)
        else:
            self._current_person = None
            self.name_label.setText("No people enrolled yet")
            self.meta_label.setText("Click 'Add Person' to create a profile.")
            self.add_photo_btn.setEnabled(False)
            self.rename_btn.setEnabled(False)
            self._clear_gallery()

    def _on_person_selected(self, row: int) -> None:
        if row < 0:
            return
        item = self.people_list.item(row)
        if not item:
            return
        pid = item.data(Qt.ItemDataRole.UserRole)
        self._current_person = self.person_repo.get_person_by_id(pid, include_faces=True)
        if self._current_person:
            self.name_label.setText(self._current_person.display_name)
            self.meta_label.setText(
                f"UUID: {self._current_person.uuid[:8]}... | "
                f"Created: {self._current_person.created_at[:10]} | "
                f"Samples: {self._current_person.sample_count}"
            )
            self.add_photo_btn.setEnabled(True)
            self.rename_btn.setEnabled(True)
            self._populate_gallery(self._current_person.reference_faces or [])

    def _clear_gallery(self) -> None:
        while self.gallery_grid.count():
            w = self.gallery_grid.takeAt(0).widget()
            if w:
                w.deleteLater()

    def _populate_gallery(self, faces: list[ReferenceFace]) -> None:
        self._clear_gallery()
        cols = 4
        for i, face in enumerate(faces):
            card = QFrame()
            card.setProperty("class", "card")
            card.setFixedSize(120, 150)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(4, 4, 4, 4)
            c_layout.setSpacing(4)

            img_lbl = QLabel()
            img_lbl.setFixedSize(110, 110)
            img_lbl.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if face.thumbnail_path and Path(face.thumbnail_path).exists():
                pix = QPixmap(face.thumbnail_path)
                scaled = pix.scaled(
                    110, 110,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                img_lbl.setPixmap(scaled)
            else:
                img_lbl.setText("Face")

            c_layout.addWidget(img_lbl)

            del_btn = QPushButton("Remove")
            del_btn.setStyleSheet("padding: 2px 4px; font-size: 10px;")
            face_id = face.id
            del_btn.clicked.connect(lambda _, fid=face_id: self._remove_reference_face(fid))
            c_layout.addWidget(del_btn)

            row = i // cols
            col = i % cols
            self.gallery_grid.addWidget(card, row, col)

        self.gallery_grid.setRowStretch(len(faces) // cols + 1, 1)

    def _add_person(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Person", "Enter person's name:")
        if ok and name.strip():
            p = self.person_repo.create_person(display_name=name.strip())
            self.refresh()
            # Select new person
            for i in range(self.people_list.count()):
                item = self.people_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == p.id:
                    self.people_list.setCurrentRow(i)
                    break

    def _rename_person(self) -> None:
        if not self._current_person:
            return
        new_name, ok = QInputDialog.getText(
            self, "Rename Person", "Enter new name:", text=self._current_person.display_name
        )
        if ok and new_name.strip() and new_name.strip() != self._current_person.display_name:
            self.person_repo.update_person_name(self._current_person.id, new_name.strip())
            self.refresh()

    def _delete_person(self) -> None:
        if not self._current_person:
            return
        confirm = QMessageBox.question(
            self,
            "Confirm Delete",
            f"Are you sure you want to delete profile '{self._current_person.display_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.person_repo.delete_person(self._current_person.id)
            self.refresh()

    def _merge_person(self) -> None:
        if not self._current_person:
            return
        all_people = self.person_repo.list_people()
        others = [p for p in all_people if p.id != self._current_person.id]
        if not others:
            QMessageBox.information(self, "Merge", "No other person profiles available to merge with.")
            return

        names = [p.display_name for p in others]
        target_name, ok = QInputDialog.getItem(
            self,
            "Merge Person",
            f"Select the person into which '{self._current_person.display_name}' should be merged:",
            names,
            editable=False,
        )
        if ok and target_name:
            target = next(p for p in others if p.display_name == target_name)
            self.person_repo.merge_people(target_person_id=target.id, source_person_id=self._current_person.id)
            QMessageBox.information(
                self,
                "Merged",
                f"Successfully merged '{self._current_person.display_name}' into '{target.display_name}'.",
            )
            self.refresh()

    def _add_reference_photo(self) -> None:
        if not self._current_person:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Reference Photo", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)"
        )
        if not file_path:
            return

        img_bgr, w, h, err = ImageReader.load_image_bgr(file_path)
        if img_bgr is None:
            QMessageBox.critical(self, "Image Error", f"Could not load image:\n{err}")
            return

        # Ensure detector is initialized
        if hasattr(self.detector, "is_ready") and not self.detector.is_ready():
            if hasattr(self.detector, "initialize"):
                self.detector.initialize()

        if hasattr(self.detector, "is_ready") and not self.detector.is_ready():
            QMessageBox.critical(
                self,
                "Model Not Ready",
                "InsightFace AI model is not ready.\n\n"
                "Please verify that the buffalo_l model package is downloaded via Home -> Manage Model."
            )
            return

        try:
            detected = self.detector.detect_faces(img_bgr)
        except Exception as e:
            QMessageBox.critical(self, "Inference Error", f"Model detection failed:\n{e}")
            return

        if not detected:
            QMessageBox.warning(
                self, "No Face Detected", "No human face was detected in this photo."
            )
            return

        chosen_face = detected[0]
        if len(detected) > 1:
            for f in detected:
                f.thumbnail_path = self.thumbnail_cache.create_face_thumbnail(img_bgr, list(f.bbox))
            dlg = FacePickerDialog(self._current_person.display_name, detected, parent=self)
            if dlg.exec() and dlg.selected_face:
                chosen_face = dlg.selected_face
            else:
                return

        emb = self.embedder.compute_embedding(img_bgr, chosen_face)
        thumb = self.thumbnail_cache.create_face_thumbnail(img_bgr, list(chosen_face.bbox))

        self.person_repo.add_reference_face(
            person_id=self._current_person.id,
            image_path=file_path,
            bbox=list(chosen_face.bbox),
            embedding=emb,
            landmarks=chosen_face.landmarks.tolist() if chosen_face.landmarks is not None else None,
            thumbnail_path=thumb,
        )

        cur_row = self.people_list.currentRow()
        self.refresh()
        self.people_list.setCurrentRow(cur_row)

    def _remove_reference_face(self, face_id: int) -> None:
        self.person_repo.remove_reference_face(face_id)
        cur_row = self.people_list.currentRow()
        self.refresh()
        self.people_list.setCurrentRow(cur_row)
