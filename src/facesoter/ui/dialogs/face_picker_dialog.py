"""
Dialog for choosing target face when a reference photo contains multiple faces.
"""

from __future__ import annotations
from typing import List, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QFrame, QRadioButton, QButtonGroup
)
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from facesoter.core.ai.provider import DetectedFace


class FacePickerDialog(QDialog):
    """Allows user to select which face is the target when importing multi-face photos."""

    def __init__(
        self,
        person_name: str,
        detected_faces: List[DetectedFace],
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.person_name = person_name
        self.detected_faces = detected_faces
        self.selected_face: Optional[DetectedFace] = None

        self.setWindowTitle("Select Target Face — FaceSoter")
        self.setMinimumWidth(540)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)

        header = QLabel(f"Multiple Faces Detected")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        instructions = QLabel(
            f"Please select which face belongs to '{self.person_name}' from the detected faces below:"
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #cccccc;")
        layout.addWidget(instructions)

        # Scroll area with face cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(230)
        container = QWidget()
        cards_layout = QHBoxLayout(container)
        cards_layout.setSpacing(12)

        self.btn_group = QButtonGroup(self)

        for i, face in enumerate(self.detected_faces):
            card = QFrame()
            card.setProperty("class", "card")
            card.setFixedWidth(130)
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(6, 6, 6, 6)
            c_layout.setSpacing(6)

            # Face thumbnail
            img_lbl = QLabel()
            img_lbl.setFixedSize(110, 110)
            img_lbl.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
            img_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if face.thumbnail_path:
                pix = QPixmap(face.thumbnail_path)
                scaled = pix.scaled(
                    110, 110,
                    Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                    Qt.TransformationMode.SmoothTransformation,
                )
                img_lbl.setPixmap(scaled)
            else:
                img_lbl.setText(f"Face #{i + 1}")

            c_layout.addWidget(img_lbl)

            # Radio button
            radio = QRadioButton(f"Face #{i + 1}")
            radio.setStyleSheet("font-weight: bold;")
            if i == 0:
                radio.setChecked(True)
            self.btn_group.addButton(radio, i)
            c_layout.addWidget(radio, alignment=Qt.AlignmentFlag.AlignCenter)

            cards_layout.addWidget(card)

        cards_layout.addStretch()
        scroll.setWidget(container)
        layout.addWidget(scroll)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        confirm_btn = QPushButton("Select Face")
        confirm_btn.setProperty("class", "btn_primary")
        confirm_btn.clicked.connect(self._on_confirm)
        btn_layout.addWidget(confirm_btn)

        layout.addLayout(btn_layout)

    def _on_confirm(self) -> None:
        idx = self.btn_group.checkedId()
        if 0 <= idx < len(self.detected_faces):
            self.selected_face = self.detected_faces[idx]
            self.accept()
        else:
            self.reject()
