"""
Safe image reader with EXIF orientation correction and format decoders.
"""

from __future__ import annotations
import os
import hashlib
from pathlib import Path
from typing import Optional, Tuple
import numpy as np
from PIL import Image, ImageOps

# Attempt to register HEIC/HEIF decoder if available
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass


class ImageReader:
    """Safely loads images with EXIF orientation correction without modifying source files."""

    SUPPORTED_EXTENSIONS = {
        ".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif", ".heic", ".heif"
    }

    @classmethod
    def is_supported(cls, file_path: Path | str) -> bool:
        """Check if file extension is supported."""
        return Path(file_path).suffix.lower() in cls.SUPPORTED_EXTENSIONS

    @staticmethod
    def compute_sha256(file_path: Path | str, chunk_size: int = 65536) -> str:
        """Compute SHA-256 hash of file content."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(chunk_size):
                hasher.update(chunk)
        return hasher.hexdigest()

    @staticmethod
    def load_image_bgr(file_path: Path | str) -> Tuple[Optional[np.ndarray], int, int, Optional[str]]:
        """
        Load an image, correct EXIF orientation, and convert to BGR NumPy array for OpenCV/ONNX.
        Returns: (image_bgr, width, height, error_message)
        """
        p = Path(file_path)
        if not p.exists():
            return None, 0, 0, f"File does not exist: {file_path}"

        try:
            # Open with Pillow to respect EXIF orientation
            with Image.open(p) as img:
                # Apply EXIF transpose in-memory
                try:
                    transposed = ImageOps.exif_transpose(img)
                except Exception:
                    transposed = img

                # Convert to RGB mode if necessary (handles CMYK, RGBA, P, etc.)
                if transposed.mode != "RGB":
                    rgb_img = transposed.convert("RGB")
                else:
                    rgb_img = transposed

                width, height = rgb_img.size
                rgb_arr = np.array(rgb_img, dtype=np.uint8)

                # Convert RGB to BGR for OpenCV/InsightFace conventions
                bgr_arr = rgb_arr[:, :, ::-1].copy()

                return bgr_arr, width, height, None

        except Exception as e:
            return None, 0, 0, f"Failed to decode image '{p.name}': {str(e)}"
