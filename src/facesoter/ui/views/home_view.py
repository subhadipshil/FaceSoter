"""
Home screen view for FaceSoter desktop application.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QTableWidget, QTableWidgetItem, QHeaderView, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from facesoter.core.database.repositories.job_repo import JobRepository, JobRecord
from facesoter.core.ai.model_downloader import ModelDownloader


class HomeView(QWidget):
    """Clean, information-dense home screen showing primary actions, recent jobs, and model status."""

    navigate_requested = Signal(str)  # "organize", "separation", "people", "jobs", "settings"
    model_setup_requested = Signal()

    def __init__(
        self,
        job_repo: JobRepository,
        downloader: ModelDownloader,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.job_repo = job_repo
        self.downloader = downloader
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(18)

        # Header
        header = QLabel("FaceSoter")
        header.setProperty("class", "page_header")
        layout.addWidget(header)

        subheader = QLabel(
            "Local-first photo organization powered by InsightFace buffalo_l. "
            "All face detection and recognition runs strictly on this computer."
        )
        subheader.setProperty("class", "page_subheader")
        layout.addWidget(subheader)

        # Mode Selection Cards
        cards_layout = QHBoxLayout()
        cards_layout.setSpacing(16)

        # Card A: Categorization
        card_a = QFrame()
        card_a.setProperty("class", "card_highlight")
        ca_layout = QVBoxLayout(card_a)
        ca_layout.setSpacing(10)

        ca_title = QLabel("Mode A: Categorization")
        ca_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        ca_desc = QLabel(
            "Sort entire collection into person folders (Mom/, Dad/). "
            "Photos with multiple people are duplicated into every matching folder. "
            "Unknown people are clustered into Person 001, Person 002. Non-face photos go to No Face."
        )
        ca_desc.setWordWrap(True)
        ca_desc.setStyleSheet("color: #cccccc; font-size: 12px;")
        ca_btn = QPushButton("Categorize Photos")
        ca_btn.setProperty("class", "btn_primary")
        ca_btn.clicked.connect(lambda: self.navigate_requested.emit("organize"))

        ca_layout.addWidget(ca_title)
        ca_layout.addWidget(ca_desc)
        ca_layout.addStretch()
        ca_layout.addWidget(ca_btn)
        cards_layout.addWidget(card_a)

        # Card B: Separation / Filter
        card_b = QFrame()
        card_b.setProperty("class", "card")
        cb_layout = QVBoxLayout(card_b)
        cb_layout.setSpacing(10)

        cb_title = QLabel("Mode B: Separation / Filter")
        cb_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        cb_desc = QLabel(
            "Filter photos matching target person profiles (e.g. Mom). "
            "Copies matching photos to SeparateFilter/Mom/ and strictly excludes "
            "them from normal categorization folders."
        )
        cb_desc.setWordWrap(True)
        cb_desc.setStyleSheet("color: #cccccc; font-size: 12px;")
        cb_btn = QPushButton("Separate / Filter")
        cb_btn.clicked.connect(lambda: self.navigate_requested.emit("separation"))

        cb_layout.addWidget(cb_title)
        cb_layout.addWidget(cb_desc)
        cb_layout.addStretch()
        cb_layout.addWidget(cb_btn)
        cards_layout.addWidget(card_b)

        layout.addLayout(cards_layout)

        # Model Status Banner
        model_frame = QFrame()
        model_frame.setProperty("class", "card")
        mf_layout = QHBoxLayout(model_frame)

        mv_layout = QVBoxLayout()
        mv_title = QLabel("AI Model Status: InsightFace buffalo_l")
        mv_title.setStyleSheet("font-weight: bold; color: #ffffff;")
        self.model_status_label = QLabel("Checking model...")
        self.model_status_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        mv_layout.addWidget(mv_title)
        mv_layout.addWidget(self.model_status_label)
        mf_layout.addLayout(mv_layout)

        mf_layout.addStretch()

        manage_model_btn = QPushButton("Manage Model...")
        manage_model_btn.clicked.connect(self.model_setup_requested.emit)
        mf_layout.addWidget(manage_model_btn)

        layout.addWidget(model_frame)

        # Recent Jobs Section
        jobs_header = QLabel("Recent Organization Jobs")
        jobs_header.setProperty("class", "section_title")
        layout.addWidget(jobs_header)

        self.jobs_table = QTableWidget(0, 5)
        self.jobs_table.setHorizontalHeaderLabels(["Name", "Mode", "Status", "Photos Processed", "Date"])
        self.jobs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.jobs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.jobs_table.setMinimumHeight(160)
        layout.addWidget(self.jobs_table)

        self.refresh()

    def refresh(self) -> None:
        """Refresh model status and recent jobs table."""
        # Refresh model status
        if self.downloader.is_installed:
            self.model_status_label.setText(
                "READY — SCRFD-10GF (det_10g.onnx) & ResNet50@WebFace600K (w600k_r50.onnx)"
            )
            self.model_status_label.setStyleSheet("color: #107c41; font-size: 12px; font-weight: 500;")
        else:
            self.model_status_label.setText(
                "NOT INSTALLED — Face recognition model package must be downloaded before scanning."
            )
            self.model_status_label.setStyleSheet("color: #d83b01; font-size: 12px; font-weight: 500;")

        # Refresh recent jobs
        jobs = self.job_repo.list_jobs(limit=10)
        self.jobs_table.setRowCount(len(jobs))
        for row, j in enumerate(jobs):
            self.jobs_table.setItem(row, 0, QTableWidgetItem(j.name))
            self.jobs_table.setItem(row, 1, QTableWidgetItem(j.mode.capitalize()))
            self.jobs_table.setItem(row, 2, QTableWidgetItem(j.status.capitalize()))
            self.jobs_table.setItem(row, 3, QTableWidgetItem(f"{j.processed_files} / {j.total_files}"))
            date_str = j.created_at[:10] if len(j.created_at) >= 10 else j.created_at
            self.jobs_table.setItem(row, 4, QTableWidgetItem(date_str))
