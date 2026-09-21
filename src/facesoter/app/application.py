"""
Application lifecycle and configuration bootstrap for FaceSoter.
"""

from __future__ import annotations
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QIcon
from facesoter.core.settings.config import ConfigManager
from facesoter.core.logging.logger import setup_logger
from facesoter.ui.main_window import MainWindow


class FaceSoterApp:
    """Manages application initialization and execution lifecycle."""

    def __init__(self, argv: list[str] | None = None):
        self.argv = argv or sys.argv
        self.config_manager = ConfigManager()
        self.logger = setup_logger(
            log_dir=self.config_manager.config.logs_dir,
            level=self.config_manager.config.log_level,
        )

    def run(self) -> int:
        """Run the desktop application."""
        self.logger.info("Starting FaceSoter desktop application...")
        app = QApplication(self.argv)
        app.setApplicationName("FaceSoter")
        app.setOrganizationName("FaceSoter")

        # Set Windows AppUserModelID so the taskbar icon displays correctly
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("FaceSoter.PhotoOrganizer.App.1.0")
        except Exception:
            pass

        # Set application icon if present
        from facesoter.ui.assets import get_asset_path
        icon_path = get_asset_path("icons/app_icon.ico")
        if not icon_path.exists():
            icon_path = get_asset_path("logo.png")

        if icon_path.exists():
            app_icon = QIcon(str(icon_path))
            app.setWindowIcon(app_icon)
        else:
            app_icon = None

        window = MainWindow(config_manager=self.config_manager)
        if app_icon:
            window.setWindowIcon(app_icon)
        window.show()

        return app.exec()
