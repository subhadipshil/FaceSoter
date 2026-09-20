"""
Settings view for FaceSoter application.
"""

from __future__ import annotations
import os
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit,
    QCheckBox, QComboBox, QDoubleSpinBox, QSpinBox, QFrame, QFileDialog,
    QMessageBox, QScrollArea
)
from facesoter.core.settings.config import ConfigManager, AppConfig
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache


class SettingsView(QWidget):
    """View for application settings and AI hyperparameters."""

    def __init__(
        self,
        config_manager: ConfigManager,
        thumbnail_cache: ThumbnailCache,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.thumbnail_cache = thumbnail_cache
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header = QLabel("Application Settings")
        header.setProperty("class", "page_header")
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        cfg = self.config_manager.config

        # 1. General Settings
        gen_card = QFrame()
        gen_card.setProperty("class", "card")
        gc_layout = QVBoxLayout(gen_card)
        gc_layout.setSpacing(10)

        gc_title = QLabel("General & File Handling")
        gc_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        gc_layout.addWidget(gc_title)

        # Default source
        gc_layout.addWidget(QLabel("Default Source Folder:"))
        s_box = QHBoxLayout()
        self.source_input = QLineEdit(cfg.default_source_dir)
        s_btn = QPushButton("Browse...")
        s_btn.clicked.connect(self._browse_source)
        s_box.addWidget(self.source_input)
        s_box.addWidget(s_btn)
        gc_layout.addLayout(s_box)

        # Default export
        gc_layout.addWidget(QLabel("Default Export Folder:"))
        e_box = QHBoxLayout()
        self.export_input = QLineEdit(cfg.default_export_dir)
        e_btn = QPushButton("Browse...")
        e_btn.clicked.connect(self._browse_export)
        e_box.addWidget(self.export_input)
        e_box.addWidget(e_btn)
        gc_layout.addLayout(e_box)

        # Checkboxes
        self.subfolders_check = QCheckBox("Include subfolders by default")
        self.subfolders_check.setChecked(cfg.include_subfolders)
        gc_layout.addWidget(self.subfolders_check)

        self.dup_check = QCheckBox("Detect exact duplicate images (SHA-256 hash comparison)")
        self.dup_check.setChecked(cfg.detect_duplicate_content)
        gc_layout.addWidget(self.dup_check)

        # Collision policy
        gc_layout.addWidget(QLabel("Filename Collision Policy:"))
        self.collision_combo = QComboBox()
        self.collision_combo.addItems([
            "Rename with number suffix (_1, _2) [Safest]",
            "Skip existing file",
            "Overwrite destination file",
        ])
        if cfg.collision_policy == "skip":
            self.collision_combo.setCurrentIndex(1)
        elif cfg.collision_policy == "overwrite":
            self.collision_combo.setCurrentIndex(2)
        else:
            self.collision_combo.setCurrentIndex(0)
        gc_layout.addWidget(self.collision_combo)

        layout.addWidget(gen_card)

        # 2. AI Parameters Card
        ai_card = QFrame()
        ai_card.setProperty("class", "card")
        ac_layout = QVBoxLayout(ai_card)
        ac_layout.setSpacing(10)

        ac_title = QLabel("AI & Inference Parameters")
        ac_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        ac_layout.addWidget(ac_title)

        # Detector confidence
        ac_layout.addWidget(QLabel("Detector Confidence Threshold (SCRFD-10GF):"))
        self.det_thresh_spin = QDoubleSpinBox()
        self.det_thresh_spin.setRange(0.10, 0.95)
        self.det_thresh_spin.setSingleStep(0.05)
        self.det_thresh_spin.setValue(cfg.detector_confidence_threshold)
        ac_layout.addWidget(self.det_thresh_spin)

        # Recognition threshold
        ac_layout.addWidget(QLabel("Face Recognition Similarity Threshold:"))
        self.rec_thresh_spin = QDoubleSpinBox()
        self.rec_thresh_spin.setRange(0.10, 0.95)
        self.rec_thresh_spin.setSingleStep(0.05)
        self.rec_thresh_spin.setValue(cfg.recognition_threshold)
        ac_layout.addWidget(self.rec_thresh_spin)

        # Clustering threshold
        ac_layout.addWidget(QLabel("Unknown People Clustering Threshold:"))
        self.clus_thresh_spin = QDoubleSpinBox()
        self.clus_thresh_spin.setRange(0.10, 0.95)
        self.clus_thresh_spin.setSingleStep(0.05)
        self.clus_thresh_spin.setValue(cfg.clustering_threshold)
        ac_layout.addWidget(self.clus_thresh_spin)

        # Min face size
        ac_layout.addWidget(QLabel("Minimum Face Size (pixels):"))
        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(16, 256)
        self.min_size_spin.setValue(cfg.min_face_size)
        ac_layout.addWidget(self.min_size_spin)

        # Execution Provider
        ac_layout.addWidget(QLabel("Execution Provider:"))
        self.provider_combo = QComboBox()
        self.provider_combo.addItems([
            "Auto (GPU if available, fallback CPU)",
            "CPU Only (Safe baseline)",
            "CUDA GPU (Requires NVIDIA CUDA)",
        ])
        if cfg.execution_provider == "cpu":
            self.provider_combo.setCurrentIndex(1)
        elif cfg.execution_provider == "cuda":
            self.provider_combo.setCurrentIndex(2)
        else:
            self.provider_combo.setCurrentIndex(0)
        ac_layout.addWidget(self.provider_combo)

        layout.addWidget(ai_card)

        # 3. Storage & Logs
        adv_card = QFrame()
        adv_card.setProperty("class", "card")
        adv_layout = QVBoxLayout(adv_card)
        adv_layout.setSpacing(10)

        adv_title = QLabel("Directories & Maintenance")
        adv_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        adv_layout.addWidget(adv_title)

        app_data_str = f"App Data Directory: {cfg.data_dir}\nDatabase: {cfg.database_path}\nModels: {cfg.models_dir}"
        data_lbl = QLabel(app_data_str)
        data_lbl.setStyleSheet("color: #888888; font-size: 11px;")
        adv_layout.addWidget(data_lbl)

        btn_row = QHBoxLayout()
        open_logs_btn = QPushButton("Open Logs Folder")
        open_logs_btn.clicked.connect(self._open_logs)
        btn_row.addWidget(open_logs_btn)

        clear_cache_btn = QPushButton("Clear Thumbnail Cache")
        clear_cache_btn.clicked.connect(self._clear_cache)
        btn_row.addWidget(clear_cache_btn)
        btn_row.addStretch()

        adv_layout.addLayout(btn_row)
        layout.addWidget(adv_card)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # Bottom save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        save_btn = QPushButton("Save Settings")
        save_btn.setProperty("class", "btn_primary")
        save_btn.clicked.connect(self._save_settings)
        save_layout.addWidget(save_btn)
        main_layout.addLayout(save_layout)

    def _browse_source(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Default Source Directory")
        if sel:
            self.source_input.setText(sel)

    def _browse_export(self) -> None:
        sel = QFileDialog.getExistingDirectory(self, "Default Export Directory")
        if sel:
            self.export_input.setText(sel)

    def _open_logs(self) -> None:
        log_dir = self.config_manager.config.logs_dir
        log_dir.mkdir(parents=True, exist_ok=True)
        os.startfile(str(log_dir))

    def _clear_cache(self) -> None:
        cnt = self.thumbnail_cache.clear()
        QMessageBox.information(self, "Cache Cleared", f"Deleted {cnt} cached thumbnails.")

    def _save_settings(self) -> None:
        coll_idx = self.collision_combo.currentIndex()
        coll_pol = "rename_numbered" if coll_idx == 0 else ("skip" if coll_idx == 1 else "overwrite")

        prov_idx = self.provider_combo.currentIndex()
        prov = "auto" if prov_idx == 0 else ("cpu" if prov_idx == 1 else "cuda")

        self.config_manager.update(
            default_source_dir=self.source_input.text().strip(),
            default_export_dir=self.export_input.text().strip(),
            include_subfolders=self.subfolders_check.isChecked(),
            detect_duplicate_content=self.dup_check.isChecked(),
            collision_policy=coll_pol,
            detector_confidence_threshold=self.det_thresh_spin.value(),
            recognition_threshold=self.rec_thresh_spin.value(),
            clustering_threshold=self.clus_thresh_spin.value(),
            min_face_size=self.min_size_spin.value(),
            execution_provider=prov,
        )
        QMessageBox.information(self, "Settings Saved", "Settings updated successfully.")
