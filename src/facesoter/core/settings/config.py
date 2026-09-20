"""
Configuration and settings management for FaceSoter.
"""

from __future__ import annotations
import os
import sys
from pathlib import Path
from dataclasses import dataclass, asdict
import json
from typing import Any, Dict


def get_default_app_data_dir() -> Path:
    """Return the standard user application data directory."""
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base = Path(local_app_data)
        else:
            base = Path.home() / "AppData" / "Local"
    else:
        base = Path.home() / ".local" / "share"
    
    app_dir = base / "FaceSoter"
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


@dataclass
class AppConfig:
    # General file settings
    default_source_dir: str = ""
    default_export_dir: str = ""
    include_subfolders: bool = True
    file_action: str = "copy"  # "copy" (default) or "move"
    collision_policy: str = "rename_numbered"  # "rename_numbered", "skip", "overwrite"
    detect_duplicate_content: bool = True
    preserve_exif: bool = True

    # AI settings
    detector_confidence_threshold: float = 0.50
    recognition_threshold: float = 0.50
    clustering_threshold: float = 0.55
    min_face_size: int = 32
    execution_provider: str = "auto"  # "auto", "cpu", "cuda"
    worker_count: int = 4
    batch_size: int = 32

    # Behavior settings
    auto_create_unknown_folders: bool = True
    separation_rule: str = "exclusive"  # "exclusive" (default) prevents leakage into normal categorized folders

    # Paths
    app_data_dir: str = ""
    custom_models_dir: str = ""
    log_level: str = "INFO"

    def __post_init__(self):
        if not self.app_data_dir:
            self.app_data_dir = str(get_default_app_data_dir())

    @property
    def data_dir(self) -> Path:
        p = Path(self.app_data_dir)
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def models_dir(self) -> Path:
        if self.custom_models_dir and Path(self.custom_models_dir).exists():
            return Path(self.custom_models_dir)
        p = self.data_dir / "models"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def thumbnails_dir(self) -> Path:
        p = self.data_dir / "thumbnails"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def logs_dir(self) -> Path:
        p = self.data_dir / "logs"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def database_path(self) -> Path:
        return self.data_dir / "facesoter.db"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> AppConfig:
        valid_keys = cls.__dataclass_fields__.keys()
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


class ConfigManager:
    """Manages reading and writing application configuration to disk."""

    def __init__(self, config_path: Path | None = None):
        if config_path is None:
            self.config_file = get_default_app_data_dir() / "settings.json"
        else:
            self.config_file = config_path
        self._config: AppConfig = self.load()

    @property
    def config(self) -> AppConfig:
        return self._config

    def load(self) -> AppConfig:
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return AppConfig.from_dict(data)
            except Exception:
                pass
        config = AppConfig()
        self.save(config)
        return config

    def save(self, config: AppConfig | None = None) -> None:
        if config is not None:
            self._config = config
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2)

    def update(self, **kwargs) -> AppConfig:
        current = self._config.to_dict()
        current.update(kwargs)
        self._config = AppConfig.from_dict(current)
        self.save()
        return self._config
