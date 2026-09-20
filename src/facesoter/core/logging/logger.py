"""
Logging configuration for FaceSoter.
"""

from __future__ import annotations
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import sys
from facesoter.core.settings.config import get_default_app_data_dir


def setup_logger(
    name: str = "facesoter",
    log_dir: Path | None = None,
    level: str = "INFO",
) -> logging.Logger:
    """Set up and configure the application logger."""
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Avoid duplicate handlers if already configured
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="[%(asctime)s] [%(levelname)s] [%(name)s:%(threadName)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handlers
    if log_dir is None:
        log_dir = get_default_app_data_dir() / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)

    # General app log (rotating 10 MB, up to 5 backups)
    app_log_file = log_dir / "facesoter.log"
    file_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Separate error log
    err_log_file = log_dir / "error.log"
    err_handler = RotatingFileHandler(
        err_log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    err_handler.setLevel(logging.ERROR)
    err_handler.setFormatter(formatter)
    logger.addHandler(err_handler)

    return logger


def get_logger(module_name: str | None = None) -> logging.Logger:
    """Get a child logger for a specific module."""
    base = logging.getLogger("facesoter")
    if module_name:
        return base.getChild(module_name)
    return base
