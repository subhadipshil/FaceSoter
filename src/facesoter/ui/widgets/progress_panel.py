"""
Progress panel widget showing live metrics, progress bar, and pause/resume/cancel controls.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QPushButton, QFrame, QGridLayout
)
from PySide6.QtCore import Qt, Signal
from facesoter.core.jobs.pipeline import PipelineProgress


class ProgressPanel(QFrame):
    """Reusable panel for displaying real-time scan metrics and controls."""

    pause_requested = Signal()
    resume_requested = Signal()
    cancel_requested = Signal()

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setProperty("class", "card")
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        # Header with Phase & Current File
        header_layout = QHBoxLayout()
        self.phase_label = QLabel("Ready")
        self.phase_label.setStyleSheet("font-weight: bold; color: #0078d4;")
        self.file_label = QLabel("")
        self.file_label.setStyleSheet("color: #888888; font-size: 11px;")
        header_layout.addWidget(self.phase_label)
        header_layout.addStretch()
        header_layout.addWidget(self.file_label)
        layout.addLayout(header_layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        # Stats Grid
        stats_layout = QGridLayout()
        stats_layout.setHorizontalSpacing(16)
        stats_layout.setVerticalSpacing(8)

        # Col 0: Files Processed
        self.processed_val = QLabel("0 / 0")
        self.processed_val.setProperty("class", "metric_value")
        self.processed_lbl = QLabel("FILES PROCESSED")
        self.processed_lbl.setProperty("class", "metric_label")
        stats_layout.addWidget(self.processed_lbl, 0, 0)
        stats_layout.addWidget(self.processed_val, 1, 0)

        # Col 1: Faces Detected
        self.faces_val = QLabel("0")
        self.faces_val.setProperty("class", "metric_value")
        self.faces_lbl = QLabel("FACES DETECTED")
        self.faces_lbl.setProperty("class", "metric_label")
        stats_layout.addWidget(self.faces_lbl, 0, 1)
        stats_layout.addWidget(self.faces_val, 1, 1)

        # Col 2: Speed
        self.speed_val = QLabel("0.0 img/s")
        self.speed_val.setProperty("class", "metric_value")
        self.speed_lbl = QLabel("PROCESSING SPEED")
        self.speed_lbl.setProperty("class", "metric_label")
        stats_layout.addWidget(self.speed_lbl, 0, 2)
        stats_layout.addWidget(self.speed_val, 1, 2)

        # Col 3: Elapsed & Remaining Time
        self.time_val = QLabel("00:00 / 00:00")
        self.time_val.setProperty("class", "metric_value")
        self.time_lbl = QLabel("ELAPSED / ETA")
        self.time_lbl.setProperty("class", "metric_label")
        stats_layout.addWidget(self.time_lbl, 0, 3)
        stats_layout.addWidget(self.time_val, 1, 3)

        layout.addLayout(stats_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.pause_btn = QPushButton("Pause")
        self.pause_btn.clicked.connect(self._on_pause_clicked)
        btn_layout.addWidget(self.pause_btn)

        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.setProperty("class", "btn_danger")
        self.cancel_btn.clicked.connect(self.cancel_requested.emit)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self._is_paused = False

    def update_progress(self, p: PipelineProgress) -> None:
        """Update metrics from PipelineProgress dataclass."""
        self.phase_label.setText(f"Status: {p.phase.capitalize()}")
        self.file_label.setText(f"File: {p.current_file}")

        if p.total_files > 0:
            pct = int((p.processed_files / p.total_files) * 100)
            self.progress_bar.setValue(min(100, pct))
            self.processed_val.setText(f"{p.processed_files} / {p.total_files}")
        else:
            self.progress_bar.setValue(0)
            self.processed_val.setText(f"{p.processed_files}")

        self.faces_val.setText(str(p.faces_detected))
        self.speed_val.setText(f"{p.speed:.1f} img/s")

        elapsed_str = self._format_seconds(p.elapsed_seconds)
        eta_str = self._format_seconds(p.remaining_seconds)
        self.time_val.setText(f"{elapsed_str} / {eta_str}")

    def _format_seconds(self, secs: float) -> str:
        s = int(secs)
        m = s // 60
        sec = s % 60
        return f"{m:02d}:{sec:02d}"

    def _on_pause_clicked(self) -> None:
        if not self._is_paused:
            self._is_paused = True
            self.pause_btn.setText("Resume")
            self.pause_requested.emit()
        else:
            self._is_paused = False
            self.pause_btn.setText("Pause")
            self.resume_requested.emit()

    def reset(self) -> None:
        """Reset panel to initial state."""
        self.progress_bar.setValue(0)
        self.phase_label.setText("Ready")
        self.file_label.setText("")
        self.processed_val.setText("0 / 0")
        self.faces_val.setText("0")
        self.speed_val.setText("0.0 img/s")
        self.time_val.setText("00:00 / 00:00")
        self.pause_btn.setText("Pause")
        self._is_paused = False
