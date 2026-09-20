"""
Directory scanner for photo discovery.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Iterator, List, Tuple, Callable, Optional
from facesoter.core.scanner.image_reader import ImageReader


class FileScanner:
    """Discovers supported photo files recursively or shallowly."""

    def __init__(self, include_subfolders: bool = True):
        self.include_subfolders = include_subfolders

    def scan_generator(
        self,
        source_dir: Path | str,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> Iterator[Path]:
        """
        Yields supported image file Paths from source_dir.
        Checks cancel_check callback if provided.
        """
        root = Path(source_dir)
        if not root.exists() or not root.is_dir():
            return

        if self.include_subfolders:
            for dirpath, _, filenames in os.walk(root):
                if cancel_check and cancel_check():
                    return
                for fname in filenames:
                    p = Path(dirpath) / fname
                    if ImageReader.is_supported(p):
                        yield p
        else:
            with os.scandir(root) as entries:
                for entry in entries:
                    if cancel_check and cancel_check():
                        return
                    if entry.is_file():
                        p = Path(entry.path)
                        if ImageReader.is_supported(p):
                            yield p

    def collect_files(
        self,
        source_dir: Path | str,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> List[Path]:
        """Scan and collect all matching file Paths."""
        return list(self.scan_generator(source_dir, cancel_check))

    def count_files(
        self,
        source_dir: Path | str,
        cancel_check: Optional[Callable[[], bool]] = None,
    ) -> int:
        """Quickly count total matching image files."""
        count = 0
        for _ in self.scan_generator(source_dir, cancel_check):
            count += 1
        return count
