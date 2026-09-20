"""
Abstract base classes and dataclasses for Face AI models.
"""

from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple, Dict, Any
import numpy as np


@dataclass
class DetectedFace:
    """Represents a face detected in an image."""
    bbox: Tuple[float, float, float, float]  # (x1, y1, x2, y2)
    score: float
    landmarks: Optional[np.ndarray] = None   # shape (5, 2)
    embedding: Optional[np.ndarray] = None   # shape (512,), float32, L2-normalized
    assigned_person_id: Optional[int] = None
    assigned_cluster_id: Optional[str] = None
    confidence: Optional[float] = None
    thumbnail_path: Optional[str] = None

    @property
    def width(self) -> float:
        return self.bbox[2] - self.bbox[0]

    @property
    def height(self) -> float:
        return self.bbox[3] - self.bbox[1]

    @property
    def size(self) -> float:
        return max(self.width, self.height)


class FaceDetectionProvider(ABC):
    """Abstract interface for face detection."""

    @abstractmethod
    def detect_faces(
        self,
        image_bgr: np.ndarray,
        threshold: float = 0.5,
        min_size: int = 32,
    ) -> List[DetectedFace]:
        """Detect faces in BGR image, returning bounding boxes and landmarks."""
        pass


class FaceEmbeddingProvider(ABC):
    """Abstract interface for face feature embedding."""

    @abstractmethod
    def compute_embedding(
        self,
        image_bgr: np.ndarray,
        face: DetectedFace,
    ) -> np.ndarray:
        """Extract 512-d L2-normalized embedding for a detected face."""
        pass

    @abstractmethod
    def compute_embeddings_batch(
        self,
        image_bgr: np.ndarray,
        faces: List[DetectedFace],
    ) -> List[np.ndarray]:
        """Extract embeddings for multiple detected faces in an image."""
        pass


class FaceModelProvider(ABC):
    """Abstract combined interface for a complete face recognition model package."""

    @abstractmethod
    def initialize(self, use_gpu: bool = False) -> bool:
        """Initialize models into memory."""
        pass

    @abstractmethod
    def is_ready(self) -> bool:
        """Check whether models are loaded and ready for inference."""
        pass

    @abstractmethod
    def get_info(self) -> Dict[str, Any]:
        """Return model metadata."""
        pass
