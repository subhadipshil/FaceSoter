"""
Main window implementation for FaceSoter.
"""

from __future__ import annotations
import threading
from pathlib import Path
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QStatusBar, QMessageBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QIcon, QPixmap

from facesoter.ui.styles.theme import DARK_THEME_QSS
from facesoter.ui.assets import get_asset_path
from facesoter.ui.dialogs.donate_dialog import DonateDialog
from facesoter.ui.views import (
    HomeView, OrganizeView, SeparationView, PeopleView, JobsView, SettingsView, AboutView
)
from facesoter.ui.dialogs.model_setup_dialog import ModelSetupDialog
from facesoter.core.settings.config import ConfigManager
from facesoter.core.database.db_manager import DatabaseManager
from facesoter.core.database.repositories import (
    PersonRepository, ImageRepository, JobRepository, SettingsRepository
)
from facesoter.core.ai.model_downloader import ModelDownloader
from facesoter.core.ai.insightface_provider import InsightFaceBuffaloLProvider
from facesoter.core.scanner.thumbnail_cache import ThumbnailCache
from facesoter.core.organizer.engine import OrganizerEngine
from facesoter.core.jobs.job_manager import JobManager
from facesoter.core.jobs.pipeline import ScanPipeline
from facesoter.core.logging.logger import get_logger

logger = get_logger("main_window")


class MainWindow(QMainWindow):
    """Primary desktop application window for FaceSoter."""

    def __init__(self, config_manager: ConfigManager):
        super().__init__()
        self.config_manager = config_manager
        self.config = config_manager.config

        # Initialize persistence & caches
        self.db_manager = DatabaseManager(self.config.database_path)
        self.person_repo = PersonRepository(self.db_manager)
        self.image_repo = ImageRepository(self.db_manager)
        self.job_repo = JobRepository(self.db_manager)
        self.settings_repo = SettingsRepository(self.db_manager)
        self.thumbnail_cache = ThumbnailCache(self.config.thumbnails_dir)

        # AI & Provider setup
        self.model_downloader = ModelDownloader(self.config.models_dir)
        self.ai_provider = InsightFaceBuffaloLProvider(self.config.models_dir)

        # Organizer Engine
        self.organizer_engine = OrganizerEngine(
            job_repo=self.job_repo,
            image_repo=self.image_repo,
        )

        # Pipeline Factory for workers
        def pipeline_factory() -> ScanPipeline:
            # Ensure AI provider is initialized before running pipeline
            if not self.ai_provider.is_ready():
                use_gpu = self.config.execution_provider in ("auto", "cuda")
                self.ai_provider.initialize(use_gpu=use_gpu)

            return ScanPipeline(
                job_repo=self.job_repo,
                image_repo=self.image_repo,
                person_repo=self.person_repo,
                detector=self.ai_provider,
                embedder=self.ai_provider,
                thumbnail_cache=self.thumbnail_cache,
            )

        self.job_manager = JobManager(
            job_repo=self.job_repo,
            pipeline_factory=pipeline_factory,
        )

        # Recover interrupted jobs from previous session
        recovered_count = self.job_repo.recover_interrupted_jobs()
        if recovered_count > 0:
            logger.info(f"Marked {recovered_count} unfinished jobs as interrupted.")

        self.setWindowTitle("FaceSoter — Windows Photo Organizer")
        self.resize(1200, 800)
        self.setStyleSheet(DARK_THEME_QSS)

        # Set main software window icon
        icon_path = get_asset_path("icons/app_icon.ico")
        if not icon_path.exists():
            icon_path = get_asset_path("logo.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._init_ui()

        # Check model on startup
        QTimer.singleShot(600, self._check_first_run_model)

    def _init_ui(self) -> None:
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Left Sidebar
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sb_layout = QVBoxLayout(sidebar)
        sb_layout.setContentsMargins(0, 0, 0, 16)
        sb_layout.setSpacing(4)

        # App Brand Header with Logo Icon
        brand_frame = QFrame()
        brand_frame.setStyleSheet("background: transparent;")
        brand_layout = QHBoxLayout(brand_frame)
        brand_layout.setContentsMargins(14, 16, 14, 8)
        brand_layout.setSpacing(10)

        logo_lbl = QLabel()
        logo_path = get_asset_path("logo.png")
        if not logo_path.exists():
            logo_path = get_asset_path("icons/app_icon.ico")
        if logo_path.exists():
            pix = QPixmap(str(logo_path)).scaled(
                36, 36, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            logo_lbl.setPixmap(pix)
            logo_lbl.setFixedSize(36, 36)
        brand_layout.addWidget(logo_lbl)

        brand_text = QVBoxLayout()
        brand_text.setSpacing(1)
        brand_text.setContentsMargins(0, 0, 0, 0)

        title_row = QHBoxLayout()
        title_row.setSpacing(6)
        app_title = QLabel("FaceSoter")
        app_title.setObjectName("app_title")
        app_title.setStyleSheet("padding: 0; margin: 0; font-size: 16px; font-weight: 800; color: #ffffff;")
        badge = QLabel("v1.1")
        badge.setObjectName("version_badge")
        title_row.addWidget(app_title)
        title_row.addWidget(badge)
        title_row.addStretch()

        app_sub = QLabel("Face-Based Photo Organizer")
        app_sub.setObjectName("app_subtitle")
        app_sub.setStyleSheet("padding: 0; margin: 0; font-size: 10px; color: #71717a;")

        brand_text.addLayout(title_row)
        brand_text.addWidget(app_sub)
        brand_layout.addLayout(brand_text)

        sb_layout.addWidget(brand_frame)

        # Navigation Buttons
        self.nav_buttons: list[QPushButton] = []

        self.btn_home = self._create_nav_btn("Home", "home")
        self.btn_organize = self._create_nav_btn("Categorize Photos", "organize")
        self.btn_separate = self._create_nav_btn("Separate / Filter", "separation")
        self.btn_people = self._create_nav_btn("People Profiles", "people")
        self.btn_jobs = self._create_nav_btn("Job History", "jobs")
        self.btn_settings = self._create_nav_btn("Settings", "settings")
        self.btn_about = self._create_nav_btn("About & Licenses", "about")

        # Subtle Buy Me a Coffee button
        self.btn_coffee = QPushButton("☕ Buy Me a Coffee")
        self.btn_coffee.setObjectName("btn_coffee")
        self.btn_coffee.clicked.connect(self._open_donate_dialog)

        sb_layout.addWidget(self.btn_home)
        sb_layout.addWidget(self.btn_organize)
        sb_layout.addWidget(self.btn_separate)
        sb_layout.addWidget(self.btn_people)
        sb_layout.addWidget(self.btn_jobs)
        sb_layout.addStretch()
        sb_layout.addWidget(self.btn_coffee)
        sb_layout.addWidget(self.btn_settings)
        sb_layout.addWidget(self.btn_about)

        main_layout.addWidget(sidebar)

        # 2. Content Stack
        self.content_stack = QStackedWidget()
        self.content_stack.setObjectName("content_area")

        # Instantiate Views
        self.home_view = HomeView(
            job_repo=self.job_repo,
            downloader=self.model_downloader,
        )
        self.home_view.navigate_requested.connect(self.navigate_to)
        self.home_view.model_setup_requested.connect(self._open_model_setup)

        self.organize_view = OrganizeView(
            job_manager=self.job_manager,
            organizer_engine=self.organizer_engine,
            job_repo=self.job_repo,
            image_repo=self.image_repo,
            person_repo=self.person_repo,
            config=self.config,
        )

        self.separation_view = SeparationView(
            job_manager=self.job_manager,
            organizer_engine=self.organizer_engine,
            job_repo=self.job_repo,
            image_repo=self.image_repo,
            person_repo=self.person_repo,
            detector=self.ai_provider,
            embedder=self.ai_provider,
            thumbnail_cache=self.thumbnail_cache,
            config=self.config,
        )

        self.people_view = PeopleView(
            person_repo=self.person_repo,
            detector=self.ai_provider,
            embedder=self.ai_provider,
            thumbnail_cache=self.thumbnail_cache,
        )

        self.jobs_view = JobsView(
            job_repo=self.job_repo,
            job_manager=self.job_manager,
        )

        self.settings_view = SettingsView(
            config_manager=self.config_manager,
            thumbnail_cache=self.thumbnail_cache,
        )

        self.about_view = AboutView()

        # Add to stack in index order
        self.view_map = {
            "home": (0, self.home_view, self.btn_home),
            "organize": (1, self.organize_view, self.btn_organize),
            "separation": (2, self.separation_view, self.btn_separate),
            "people": (3, self.people_view, self.btn_people),
            "jobs": (4, self.jobs_view, self.btn_jobs),
            "settings": (5, self.settings_view, self.btn_settings),
            "about": (6, self.about_view, self.btn_about),
        }

        self.content_stack.addWidget(self.home_view)
        self.content_stack.addWidget(self.organize_view)
        self.content_stack.addWidget(self.separation_view)
        self.content_stack.addWidget(self.people_view)
        self.content_stack.addWidget(self.jobs_view)
        self.content_stack.addWidget(self.settings_view)
        self.content_stack.addWidget(self.about_view)

        main_layout.addWidget(self.content_stack)

        # 3. Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.model_status_btn = QPushButton("Model: Checking...")
        self.model_status_btn.setStyleSheet("border: none; background: transparent; color: #888888;")
        self.model_status_btn.clicked.connect(self._open_model_setup)
        self.status_bar.addWidget(self.model_status_btn)

        self.status_bar.addPermanentWidget(
            QLabel("100% Local Inference | No Cloud Uploads")
        )

        self.navigate_to("home")
        self._update_model_status_bar()

    def _create_nav_btn(self, label: str, target: str) -> QPushButton:
        btn = QPushButton(label)
        btn.setProperty("class", "nav_btn")
        btn.setCheckable(True)
        btn.clicked.connect(lambda: self.navigate_to(target))
        self.nav_buttons.append(btn)
        return btn

    def navigate_to(self, target: str) -> None:
        if target not in self.view_map:
            return
        idx, view, btn = self.view_map[target]
        self.content_stack.setCurrentIndex(idx)

        # Update button active states
        for b in self.nav_buttons:
            b.setChecked(b == btn)
            b.setProperty("active", "true" if b == btn else "false")
            b.style().unpolish(b)
            b.style().polish(b)

        # Refresh views if applicable
        if hasattr(view, "refresh"):
            view.refresh()
        if hasattr(view, "refresh_people"):
            view.refresh_people()

    def _check_first_run_model(self) -> None:
        if not self.model_downloader.is_installed:
            self._open_model_setup()
        else:
            self._ensure_ai_initialized()

    def _ensure_ai_initialized(self) -> None:
        """Warm up AI model in background thread so inference is instant."""
        if self.ai_provider.is_ready():
            return
        use_gpu = self.config.execution_provider in ("auto", "cuda")
        threading.Thread(
            target=lambda: self.ai_provider.initialize(use_gpu=use_gpu),
            daemon=True,
            name="AI-Initializer",
        ).start()

    def _open_model_setup(self) -> None:
        dlg = ModelSetupDialog(self.model_downloader, parent=self)
        dlg.exec()
        self._update_model_status_bar()
        self.home_view.refresh()
        if self.model_downloader.is_installed:
            self._ensure_ai_initialized()

    def _update_model_status_bar(self) -> None:
        if self.model_downloader.is_installed:
            self.model_status_btn.setText("● buffalo_l: Ready")
            self.model_status_btn.setStyleSheet(
                "border: none; background: transparent; color: #107c41; font-weight: bold;"
            )
        else:
            self.model_status_btn.setText("▲ buffalo_l: Setup Required")
            self.model_status_btn.setStyleSheet(
                "border: none; background: transparent; color: #d83b01; font-weight: bold;"
            )

    def _open_donate_dialog(self) -> None:
        """Open subtle Buy Me a Coffee / Support dialog."""
        dlg = DonateDialog(parent=self)
        dlg.exec()

