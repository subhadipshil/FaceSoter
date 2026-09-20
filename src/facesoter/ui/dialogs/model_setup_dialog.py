"""
Model Setup and Download Wizard for InsightFace buffalo_l.
"""

from __future__ import annotations
import os
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QProgressBar,
    QFileDialog, QMessageBox, QFrame, QTextEdit
)
from PySide6.QtCore import Qt, Signal, QObject
from facesoter.core.ai.model_downloader import ModelDownloader, OFFICIAL_BUFFALO_L_URL
from facesoter.core.logging.logger import get_logger

logger = get_logger("model_setup_dialog")


class DownloadSignalBridge(QObject):
    progress = Signal(int, int, float)  # downloaded, total, speed
    finished = Signal(bool, str)        # success, message


class ModelSetupDialog(QDialog):
    """First-run and settings wizard for downloading and verifying buffalo_l."""

    def __init__(self, downloader: ModelDownloader, parent=None):
        super().__init__(parent)
        self.downloader = downloader
        self.bridge = DownloadSignalBridge()
        self.bridge.progress.connect(self._on_progress)
        self.bridge.finished.connect(self._on_finished)

        self._download_thread: threading.Thread | None = None
        self.setWindowTitle("Face Recognition Model Setup — FaceSoter")
        self.setMinimumWidth(620)
        self.setModal(True)
        self._init_ui()
        self._check_initial_status()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title & Subtitle
        title = QLabel("InsightFace Buffalo_L Setup")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        layout.addWidget(title)

        subtitle = QLabel(
            "FaceSoter requires the official InsightFace buffalo_l model package "
            "for local face detection (SCRFD-10GF) and recognition (ResNet50@WebFace600K)."
        )
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        layout.addWidget(subtitle)

        # License Notice Card
        notice_card = QFrame()
        notice_card.setProperty("class", "card")
        notice_layout = QVBoxLayout(notice_card)
        notice_layout.setContentsMargins(12, 10, 12, 10)

        notice_title = QLabel("ATTRIBUTION & NON-COMMERCIAL RESEARCH TERMS:")
        notice_title.setStyleSheet("font-weight: bold; color: #e5a00d; font-size: 11px;")
        notice_layout.addWidget(notice_title)

        notice_text = QLabel(
            "• Upstream Project: InsightFace (deepinsight/insightface)\n"
            "• Detector: SCRFD-10GF (det_10g.onnx) | Recognizer: ResNet50@WebFace600K (w600k_r50.onnx)\n"
            "• License Terms: InsightFace pre-trained models are for NON-COMMERCIAL RESEARCH PURPOSES ONLY.\n"
            "• Download Source: Official GitHub release archive (~326 MB). Downloaded once and cached locally."
        )
        notice_text.setStyleSheet("color: #cccccc; font-size: 11px; line-height: 1.4;")
        notice_text.setWordWrap(True)
        notice_layout.addWidget(notice_text)
        layout.addWidget(notice_card)

        # Status & Details
        status_box = QFrame()
        status_box.setProperty("class", "card")
        sb_layout = QVBoxLayout(status_box)
        sb_layout.setContentsMargins(12, 10, 12, 10)

        self.status_label = QLabel("Status: Checking model files...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #ffffff;")
        sb_layout.addWidget(self.status_label)

        self.location_label = QLabel(f"Storage Location: {self.downloader.model_dir}")
        self.location_label.setStyleSheet("color: #888888; font-size: 11px;")
        self.location_label.setWordWrap(True)
        sb_layout.addWidget(self.location_label)
        layout.addWidget(status_box)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.progress_detail = QLabel("")
        self.progress_detail.setStyleSheet("color: #888888; font-size: 11px;")
        self.progress_detail.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.progress_detail.setVisible(False)
        layout.addWidget(self.progress_detail)

        # Buttons
        btn_layout = QHBoxLayout()
        self.open_folder_btn = QPushButton("Open Model Folder")
        self.open_folder_btn.clicked.connect(self._open_model_folder)
        btn_layout.addWidget(self.open_folder_btn)

        self.use_existing_btn = QPushButton("Use Existing Model Folder...")
        self.use_existing_btn.clicked.connect(self._use_existing_folder)
        btn_layout.addWidget(self.use_existing_btn)

        btn_layout.addStretch()

        self.download_btn = QPushButton("Download & Install")
        self.download_btn.setProperty("class", "btn_primary")
        self.download_btn.clicked.connect(self._start_download)
        btn_layout.addWidget(self.download_btn)

        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)

    def _check_initial_status(self) -> None:
        installed = self.downloader.is_installed
        if installed:
            self.status_label.setText("Status: READY (Installed & Verified)")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #107c41;")
            self.download_btn.setText("Re-Download Model")
        else:
            self.status_label.setText("Status: NOT INSTALLED (~326 MB required)")
            self.status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #d83b01;")
            self.download_btn.setText("Download & Install")

    def _open_model_folder(self) -> None:
        folder = self.downloader.model_dir
        folder.mkdir(parents=True, exist_ok=True)
        os.startfile(str(folder))

    def _use_existing_folder(self) -> None:
        selected = QFileDialog.getExistingDirectory(
            self, "Select Folder Containing buffalo_l ONNX Models", str(Path.home())
        )
        if selected:
            sel_path = Path(selected)
            try:
                self.downloader.install_from_local_folder(sel_path)
                QMessageBox.information(
                    self, "Success", "Model files successfully validated and linked!"
                )
                self._check_initial_status()
            except Exception as e:
                QMessageBox.critical(
                    self, "Validation Failed", f"Could not validate model folder:\n\n{str(e)}"
                )

    def _start_download(self) -> None:
        self.download_btn.setEnabled(False)
        self.use_existing_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.progress_detail.setVisible(True)
        self.status_label.setText("Status: Downloading official buffalo_l package...")
        self.status_label.setStyleSheet("font-weight: bold; font-size: 13px; color: #0078d4;")

        def worker():
            try:
                def progress_cb(dl, total, speed):
                    self.bridge.progress.emit(dl, total, speed)

                ok = self.downloader.download_and_install(progress_callback=progress_cb)
                if ok:
                    self.bridge.finished.emit(True, "Model successfully downloaded and verified!")
                else:
                    self.bridge.finished.emit(False, "Download was cancelled.")
            except Exception as e:
                self.bridge.finished.emit(False, str(e))

        self._download_thread = threading.Thread(target=worker, daemon=True)
        self._download_thread.start()

    def _on_progress(self, dl: int, total: int, speed: float) -> None:
        dl_mb = dl / (1024 * 1024)
        total_mb = total / (1024 * 1024) if total > 0 else 326.0
        speed_mb = speed / (1024 * 1024)

        if total > 0:
            pct = int((dl / total) * 100)
            self.progress_bar.setValue(min(100, pct))
            self.progress_detail.setText(
                f"{dl_mb:.1f} MB / {total_mb:.1f} MB ({pct}%) — {speed_mb:.2f} MB/s"
            )
        else:
            self.progress_detail.setText(f"{dl_mb:.1f} MB downloaded — {speed_mb:.2f} MB/s")

    def _on_finished(self, success: bool, message: str) -> None:
        self.download_btn.setEnabled(True)
        self.use_existing_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.progress_detail.setVisible(False)

        if success:
            QMessageBox.information(self, "Installation Complete", message)
            self._check_initial_status()
        else:
            help_text = (
                f"Model installation error:\n\n{message}\n\n"
                "Tip: If your firewall or proxy prevents automated download:\n"
                "1. Download buffalo_l.zip manually from:\n"
                f"   {OFFICIAL_BUFFALO_L_URL}\n"
                "2. Extract the archive into a folder.\n"
                "3. Click 'Use Existing Model Folder...' to link the files directly."
            )
            QMessageBox.critical(self, "Download Failed", help_text)
            self._check_initial_status()
