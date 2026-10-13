"""
Review dialog for Single and Group photo separation before file operations commence.
Displays clear metric counts for Single photos, Group photos, No Face photos, and destination tree.
"""

from __future__ import annotations
from typing import Dict, List
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGridLayout, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt
from facesoter.core.organizer.engine import PreCopySummary


class SingleGroupReviewDialog(QDialog):
    """Pre-copy review dialog tailored for Single & Group Photo Separation."""

    def __init__(
        self,
        summary: PreCopySummary,
        single_count: int,
        group_count: int,
        no_face_count: int,
        is_move: bool = False,
        parent=None,
    ):
        super().__init__(parent)
        self.summary = summary
        self.single_count = single_count
        self.group_count = group_count
        self.no_face_count = no_face_count
        self.is_move = is_move

        self.setWindowTitle("Review Single & Group Photo Plan — FaceSoter")
        self.setMinimumSize(700, 480)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header = QLabel("Single & Group Separation Breakdown")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(header)

        sub = QLabel(
            "Review detected face breakdown across your photo collection before copying."
        )
        sub.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        main_layout.addWidget(sub)

        # Metric Cards
        metrics_frame = QFrame()
        metrics_frame.setProperty("class", "card")
        m_layout = QGridLayout(metrics_frame)
        m_layout.setHorizontalSpacing(20)
        m_layout.setVerticalSpacing(8)

        metrics = [
            ("TOTAL SCANNED", str(self.summary.photos_scanned), "#e4e4e7"),
            ("SINGLE PHOTOS (1 Face)", str(self.single_count), "#38bdf8"),
            ("GROUP PHOTOS (2+ Faces)", str(self.group_count), "#a855f7"),
            ("NO FACE DETECTED", str(self.no_face_count), "#71717a"),
        ]

        for col, (label, val, color) in enumerate(metrics):
            lbl = QLabel(label)
            lbl.setProperty("class", "metric_label")
            lbl.setStyleSheet("color: #71717a; font-size: 10px; font-weight: 700;")
            vl = QLabel(val)
            vl.setProperty("class", "metric_value")
            vl.setStyleSheet(f"color: {color}; font-size: 22px; font-weight: 800;")
            m_layout.addWidget(lbl, 0, col)
            m_layout.addWidget(vl, 1, col)

        main_layout.addWidget(metrics_frame)

        # Destination Folder Tree Preview
        tree_label = QLabel("Planned Destination Folders:")
        tree_label.setStyleSheet("font-weight: bold; color: #ffffff; font-size: 13px;")
        main_layout.addWidget(tree_label)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Destination Folder", "Photos to Copy" if not self.is_move else "Photos to Move"])
        self.tree.setColumnWidth(0, 380)

        for folder, count in sorted(self.summary.destination_tree.items()):
            item = QTreeWidgetItem([folder, str(count)])
            self.tree.addTopLevelItem(item)

        main_layout.addWidget(self.tree)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        action_text = "Start Move Operations" if self.is_move else "Start Copy Operations"
        self.start_btn = QPushButton(action_text)
        self.start_btn.setProperty("class", "btn_primary")
        self.start_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.start_btn)

        main_layout.addLayout(btn_layout)
