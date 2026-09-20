"""
Thumbnail card widget for displaying face clusters and person profiles.
"""

from __future__ import annotations
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QInputDialog
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, Signal


class ThumbnailCard(QFrame):
    """Card showing face thumbnail, person name, photo count, and rename trigger."""

    name_changed = Signal(str, str)  # old_name, new_name

    def __init__(
        self,
        identifier: str,
        name: str,
        sample_count: int,
        thumbnail_path: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.identifier = identifier
        self.name = name
        self.sample_count = sample_count
        self.thumbnail_path = thumbnail_path

        self.setProperty("class", "card")
        self.setFixedWidth(160)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Image thumbnail
        self.img_label = QLabel()
        self.img_label.setFixedSize(144, 144)
        self.img_label.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._load_thumbnail()
        layout.addWidget(self.img_label)

        # Name label
        self.name_label = QLabel(self.name)
        self.name_label.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.name_label)

        # Sample count badge
        count_str = f"{self.sample_count} {'photo' if self.sample_count == 1 else 'photos'}"
        self.count_label = QLabel(count_str)
        self.count_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.count_label)

        # Rename button
        self.rename_btn = QPushButton("Rename")
        self.rename_btn.setStyleSheet("padding: 4px 8px; font-size: 11px;")
        self.rename_btn.clicked.connect(self._on_rename)
        layout.addWidget(self.rename_btn)

    def _load_thumbnail(self) -> None:
        if self.thumbnail_path and Path(self.thumbnail_path).exists():
            pix = QPixmap(self.thumbnail_path)
            scaled = pix.scaled(
                144, 144,
                Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.img_label.setPixmap(scaled)
        else:
            self.img_label.setText("No Preview")

    def _on_rename(self) -> None:
        new_name, ok = QInputDialog.getText(
            self, "Rename Person", "Enter new name:", text=self.name
        )
        if ok and new_name.strip() and new_name.strip() != self.name:
            old_name = self.name
            self.name = new_name.strip()
            self.name_label.setText(self.name)
            self.name_changed.emit(old_name, self.name)
