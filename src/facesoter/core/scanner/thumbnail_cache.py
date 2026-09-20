"""
Disk-based thumbnail cache for face crops and image previews.
"""

from __future__ import annotations
import uuid
from pathlib import Path
from typing import Optional, List
import numpy as np
from PIL import Image


class ThumbnailCache:
    """Manages cached thumbnails on disk for UI performance."""

    def __init__(self, cache_dir: Path, thumb_size: int = 160):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thumb_size = thumb_size

    def create_face_thumbnail(
        self,
        image_bgr: np.ndarray,
        bbox: List[float],
        prefix: str = "face",
        margin_ratio: float = 0.20,
    ) -> str:
        """
        Crop a face from the image with a margin and save as JPEG thumbnail.
        Returns the absolute path to the thumbnail file.
        """
        img_h, img_w = image_bgr.shape[:2]
        x1, y1, x2, y2 = bbox

        w = x2 - x1
        h = y2 - y1
        margin_x = w * margin_ratio
        margin_y = h * margin_ratio

        crop_x1 = max(0, int(x1 - margin_x))
        crop_y1 = max(0, int(y1 - margin_y))
        crop_x2 = min(img_w, int(x2 + margin_x))
        crop_y2 = min(img_h, int(y2 + margin_y))

        if crop_x2 <= crop_x1 or crop_y2 <= crop_y1:
            crop_bgr = image_bgr
        else:
            crop_bgr = image_bgr[crop_y1:crop_y2, crop_x1:crop_x2]

        # Convert BGR crop to RGB PIL Image
        crop_rgb = crop_bgr[:, :, ::-1]
        pil_img = Image.fromarray(crop_rgb)
        pil_img.thumbnail((self.thumb_size, self.thumb_size), Image.Resampling.LANCZOS)

        thumb_name = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
        thumb_path = self.cache_dir / thumb_name
        pil_img.save(thumb_path, format="JPEG", quality=85)
        return str(thumb_path)

    def create_image_thumbnail(
        self,
        image_bgr: np.ndarray,
        prefix: str = "img",
        max_size: int = 240,
    ) -> str:
        """Create a scaled down preview of an entire image."""
        rgb_arr = image_bgr[:, :, ::-1]
        pil_img = Image.fromarray(rgb_arr)
        pil_img.thumbnail((max_size, max_size), Image.Resampling.BILINEAR)

        thumb_name = f"{prefix}_{uuid.uuid4().hex[:12]}.jpg"
        thumb_path = self.cache_dir / thumb_name
        pil_img.save(thumb_path, format="JPEG", quality=80)
        return str(thumb_path)

    def clear(self) -> int:
        """Remove all cached thumbnails. Returns count of deleted files."""
        count = 0
        for item in self.cache_dir.iterdir():
            if item.is_file() and item.suffix.lower() == ".jpg":
                try:
                    item.unlink()
                    count += 1
                except Exception:
                    pass
        return count
