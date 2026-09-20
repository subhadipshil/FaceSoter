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

        # Set application icon if present
        icon_path = Path(__file__).resolve().parent.parent.parent.parent / "assets" / "icons" / "app_icon.ico"
        if icon_path.exists():
            app.setWindowIcon(QIcon(str(icon_path)))

        window = MainWindow(config_manager=self.config_manager)
        window.show()

        return app.exec()
