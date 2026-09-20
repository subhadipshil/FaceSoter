"""
Pre-copy review dialog displaying detected clusters, statistics, and folder preview.
"""

from __future__ import annotations
from typing import List, Dict, Callable, Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QScrollArea,
    QWidget, QFrame, QGridLayout, QTreeWidget, QTreeWidgetItem, QSplitter
)
from PySide6.QtCore import Qt, Signal
from facesoter.ui.widgets.thumbnail_card import ThumbnailCard
from facesoter.core.organizer.engine import PreCopySummary


class ReviewDialog(QDialog):
    """Review screen shown after scanning completes before disk copy begins."""

    rename_requested = Signal(str, str)  # old_name, new_name

    def __init__(
        self,
        summary: PreCopySummary,
        cluster_items: List[Dict[str, any]],  # [{id, name, count, thumb_path}, ...]
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.summary = summary
        self.cluster_items = cluster_items

        self.setWindowTitle("Review Detected People & Pre-Copy Summary — FaceSoter")
        self.setMinimumSize(880, 640)
        self.setModal(True)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QLabel("Review Scan Results & Organization Plan")
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        main_layout.addWidget(header)

        # Summary Metric Cards
        metrics_frame = QFrame()
        metrics_frame.setProperty("class", "card")
        m_layout = QGridLayout(metrics_frame)
        m_layout.setHorizontalSpacing(24)

        metrics = [
            ("PHOTOS SCANNED", str(self.summary.photos_scanned)),
            ("WITH FACES", str(self.summary.photos_with_faces)),
            ("NO FACE", str(self.summary.photos_without_faces)),
            ("PEOPLE DETECTED", str(self.summary.people_detected)),
            ("FILES TO COPY", str(self.summary.total_copies_to_perform)),
        ]

        for col, (label, val) in enumerate(metrics):
            lbl = QLabel(label)
            lbl.setProperty("class", "metric_label")
            vl = QLabel(val)
            vl.setProperty("class", "metric_value")
            m_layout.addWidget(lbl, 0, col)
            m_layout.addWidget(vl, 1, col)

        main_layout.addWidget(metrics_frame)

        # Splitter between People Grid and Destination Tree
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: People Clusters Grid
        people_widget = QWidget()
        pw_layout = QVBoxLayout(people_widget)
        pw_layout.setContentsMargins(0, 0, 0, 0)

        pw_title = QLabel("Detected People (Click Rename to customize folder names)")
        pw_title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 12px;")
        pw_layout.addWidget(pw_title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        grid_container = QWidget()
        self.grid_layout = QGridLayout(grid_container)
        self.grid_layout.setSpacing(10)

        cols = 3
        for i, item in enumerate(self.cluster_items):
            card = ThumbnailCard(
                identifier=item.get("id", f"c_{i}"),
                name=item.get("name", f"Person {i + 1}"),
                sample_count=item.get("count", 1),
                thumbnail_path=item.get("thumb_path"),
            )
            card.name_changed.connect(self._on_person_renamed)
            row = i // cols
            col = i % cols
            self.grid_layout.addWidget(card, row, col)

        self.grid_layout.setRowStretch(len(self.cluster_items) // cols + 1, 1)
        scroll.setWidget(grid_container)
        pw_layout.addWidget(scroll)
        splitter.addWidget(people_widget)

        # Right: Folder Tree Preview
        tree_widget = QWidget()
        tw_layout = QVBoxLayout(tree_widget)
        tw_layout.setContentsMargins(0, 0, 0, 0)

        tw_title = QLabel("Planned Destination Folders")
        tw_title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 12px;")
        tw_layout.addWidget(tw_title)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Folder / Category", "Photo Count"])
        self.tree.setColumnWidth(0, 240)
        self._populate_tree()
        tw_layout.addWidget(self.tree)

        splitter.addWidget(tree_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel Scan")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.start_copy_btn = QPushButton("Start Organization (Copy Files)")
        self.start_copy_btn.setProperty("class", "btn_primary")
        self.start_copy_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.start_copy_btn)

        main_layout.addLayout(btn_layout)

    def _populate_tree(self) -> None:
        self.tree.clear()
        for folder, count in sorted(self.summary.destination_tree.items()):
            item = QTreeWidgetItem([folder, str(count)])
            self.tree.addTopLevelItem(item)

    def _on_person_renamed(self, old_name: str, new_name: str) -> None:
        self.rename_requested.emit(old_name, new_name)
        # Update destination tree preview
        old_rel = f"Categorized/{old_name}"
        new_rel = f"Categorized/{new_name}"
        if old_rel in self.summary.destination_tree:
            count = self.summary.destination_tree.pop(old_rel)
            self.summary.destination_tree[new_rel] = count
            self._populate_tree()
