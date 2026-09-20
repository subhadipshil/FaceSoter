"""
Atomic, safe file copier with collision handling, disk space checks, and EXIF preservation.
"""

from __future__ import annotations
import os
import shutil
import uuid
from pathlib import Path
from typing import Tuple, Optional
from facesoter.core.scanner.image_reader import ImageReader
from facesoter.core.logging.logger import get_logger

logger = get_logger("file_copier")


class FileCopyError(Exception):
    """Raised when file copying fails."""
    pass


class SafeFileCopier:
    """Performs atomic file copies while preserving EXIF, timestamps, and resolving collisions."""

    def __init__(
        self,
        collision_policy: str = "rename_numbered",  # "rename_numbered", "skip", "overwrite"
        detect_duplicates: bool = True,
    ):
        self.collision_policy = collision_policy
        self.detect_duplicates = detect_duplicates

    @staticmethod
    def check_disk_space(target_dir: Path, required_bytes: int) -> bool:
        """Check if destination directory has at least required_bytes free space + 50 MB safety margin."""
        try:
            total, used, free = shutil.disk_usage(target_dir)
            return free > (required_bytes + 50 * 1024 * 1024)
        except Exception:
            return True  # If unable to query disk usage, proceed with caution

    def resolve_destination_path(
        self,
        source_path: Path,
        destination_dir: Path,
    ) -> Tuple[Optional[Path], bool]:
        """
        Determine the final destination path based on collision policy.
        Returns: (final_path, should_skip)
        """
        destination_dir.mkdir(parents=True, exist_ok=True)
        dest_path = destination_dir / source_path.name

        if not dest_path.exists():
            return dest_path, False

        # Collision detected
        if self.collision_policy == "skip":
            return dest_path, True

        if self.collision_policy == "overwrite":
            return dest_path, False

        # If policy is rename_numbered, check if contents are identical
        if self.detect_duplicates:
            try:
                src_size = source_path.stat().st_size
                dest_size = dest_path.stat().st_size
                if src_size == dest_size:
                    src_hash = ImageReader.compute_sha256(source_path)
                    dest_hash = ImageReader.compute_sha256(dest_path)
                    if src_hash == dest_hash:
                        # Identical file already exists at destination
                        return dest_path, True
            except Exception:
                pass

        # Generate numbered name: name_1.ext, name_2.ext, etc.
        stem = source_path.stem
        suffix = source_path.suffix
        counter = 1
        while True:
            candidate = destination_dir / f"{stem}_{counter}{suffix}"
            if not candidate.exists():
                return candidate, False
            counter += 1

    def copy_file_atomic(
        self,
        source_path: Path | str,
        destination_dir: Path | str,
        move: bool = False,
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Copy or move a file atomically to destination_dir.
        Returns: (success: bool, final_path: str, error_message: Optional[str])
        """
        src = Path(source_path)
        dest_dir = Path(destination_dir)

        if not src.exists():
            return False, "", f"Source file does not exist: {src}"

        try:
            file_size = src.stat().st_size
        except Exception as e:
            return False, "", f"Cannot read source file: {e}"

        # Check destination disk space
        if not self.check_disk_space(dest_dir, file_size):
            return False, "", f"Insufficient free disk space in: {dest_dir}"

        target_path, should_skip = self.resolve_destination_path(src, dest_dir)
        if should_skip:
            return True, str(target_path), "Skipped: identical file already exists"

        if target_path is None:
            return False, "", "Failed to resolve destination path"

        # Atomic copy using temporary file in same directory
        temp_name = f".tmp_facesoter_{uuid.uuid4().hex[:8]}_{target_path.name}"
        temp_path = dest_dir / temp_name

        try:
            # Copy data and preserve timestamps / EXIF metadata
            shutil.copy2(src, temp_path)

            # Flush to disk
            with open(temp_path, "ab") as f:
                f.flush()
                os.fsync(f.fileno())

            # Atomic rename/replace
            temp_path.replace(target_path)

            if move:
                try:
                    src.unlink()
                except Exception as e:
                    logger.warning(f"File copied but source could not be deleted during move: {e}")

            return True, str(target_path), None

        except Exception as e:
            if temp_path.exists():
                try:
                    temp_path.unlink()
                except Exception:
                    pass
            return False, "", f"Copy failed: {str(e)}"
