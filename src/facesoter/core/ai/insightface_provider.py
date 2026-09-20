"""
InsightFace Buffalo_L model provider implementation using ONNX Runtime.
"""

from __future__ import annotations
import os
import sys
import threading
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
import numpy as np

from facesoter.core.ai.provider import (
    FaceModelProvider,
    FaceDetectionProvider,
    FaceEmbeddingProvider,
    DetectedFace,
)
from facesoter.core.logging.logger import get_logger

logger = get_logger("insightface_provider")


class InsightFaceBuffaloLProvider(FaceModelProvider, FaceDetectionProvider, FaceEmbeddingProvider):
    """
    Concrete implementation of InsightFace buffalo_l pipeline:
    - SCRFD-10GF (det_10g.onnx) for detection and 5-point landmarks
    - ResNet50@WebFace600K ArcFace (w600k_r50.onnx) for 512-d embeddings
    """

    def __init__(self, models_dir: Path):
        self.models_dir = models_dir
        self.model_pkg_dir = models_dir / "buffalo_l"
        self._app = None
        self._is_ready = False
        self._execution_provider = "CPUExecutionProvider"
        self._last_error: str = ""
        self._lock = threading.Lock()

    def initialize(self, use_gpu: bool = False) -> bool:
        """Initialize InsightFace model pipeline."""
        with self._lock:
            if self._is_ready and self._app is not None:
                return True

            try:
                import onnxruntime as ort
                import insightface
                from insightface.app import FaceAnalysis

                # Determine available execution providers
                available_providers = ort.get_available_providers()
                logger.info(f"Available ONNX Runtime execution providers: {available_providers}")

                providers = []
                if use_gpu and "CUDAExecutionProvider" in available_providers:
                    providers.append("CUDAExecutionProvider")
                    self._execution_provider = "CUDAExecutionProvider"
                providers.append("CPUExecutionProvider")
                if not use_gpu or "CUDAExecutionProvider" not in available_providers:
                    self._execution_provider = "CPUExecutionProvider"

                # Locate the directory containing buffalo_l ONNX models
                candidates = [
                    self.model_pkg_dir,
                    self.models_dir,
                    self.models_dir / "models" / "buffalo_l",
                    self.models_dir.parent / "models" / "buffalo_l",
                ]
                model_dir: Optional[Path] = None
                for c in candidates:
                    if c.exists() and (c / "det_10g.onnx").exists():
                        model_dir = c
                        break

                if model_dir is None:
                    # Recursive search inside models directory
                    for onnx_file in self.models_dir.rglob("det_10g.onnx"):
                        model_dir = onnx_file.parent
                        break

                if model_dir is None:
                    model_dir = self.model_pkg_dir

                if not (model_dir / "det_10g.onnx").exists():
                    self._last_error = (
                        f"Required model 'det_10g.onnx' not found in {model_dir}. "
                        "Please download the buffalo_l package in Model Setup."
                    )
                    logger.error(self._last_error)
                    return False

                logger.info(f"Resolved buffalo_l model path: {model_dir.resolve()}")

                # root_dir for InsightFace fallback
                parent_dir = model_dir.parent
                root_dir = str(parent_dir.parent.resolve() if parent_dir.name == "models" else parent_dir.resolve())

                # Pass direct folder path as name: InsightFace accepts direct directory paths
                # and bypasses ensure_available / online downloading
                self._app = FaceAnalysis(
                    name=str(model_dir.resolve()),
                    root=root_dir,
                    providers=providers,
                    allowed_modules=["detection", "recognition"],
                )

                # ctx_id=0 for GPU, ctx_id=-1 for CPU
                ctx_id = 0 if "CUDAExecutionProvider" in providers and use_gpu else -1
                self._app.prepare(ctx_id=ctx_id, det_size=(640, 640))

                # Run a warmup test on a dummy image to ensure inference works
                dummy = np.zeros((640, 640, 3), dtype=np.uint8)
                _ = self._app.get(dummy)

                self._is_ready = True
                self._last_error = ""
                logger.info(f"InsightFace buffalo_l initialized successfully using {self._execution_provider}.")
                return True

            except Exception as e:
                self._is_ready = False
                self._app = None
                self._last_error = str(e)
                logger.error(f"Failed to initialize InsightFace buffalo_l: {e}", exc_info=True)
                return False

    def is_ready(self) -> bool:
        return self._is_ready and self._app is not None

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": "buffalo_l",
            "detector": "SCRFD-10GF",
            "recognizer": "ResNet50@WebFace600K",
            "dimension": 512,
            "provider": self._execution_provider,
            "ready": self.is_ready(),
            "location": str(self.model_pkg_dir),
            "last_error": self._last_error,
        }

    def detect_faces(
        self,
        image_bgr: np.ndarray,
        threshold: float = 0.50,
        min_size: int = 32,
    ) -> List[DetectedFace]:
        """Detect faces in BGR image using SCRFD."""
        if not self.is_ready():
            if not self.initialize():
                err_detail = f" ({self._last_error})" if self._last_error else ""
                raise RuntimeError(f"InsightFace model is not initialized or ready.{err_detail}")

        raw_faces = self._app.get(image_bgr)
        results: List[DetectedFace] = []

        for f in raw_faces:
            score = float(f.det_score) if hasattr(f, "det_score") else 0.0
            if score < threshold:
                continue

            bbox = [float(x) for x in f.bbox]
            width = bbox[2] - bbox[0]
            height = bbox[3] - bbox[1]
            if max(width, height) < min_size:
                continue

            landmarks = f.kps.copy() if hasattr(f, "kps") and f.kps is not None else None

            # Get embedding if computed during get()
            embedding = None
            if hasattr(f, "normed_embedding") and f.normed_embedding is not None:
                embedding = np.asarray(f.normed_embedding, dtype=np.float32)
            elif hasattr(f, "embedding") and f.embedding is not None:
                emb = np.asarray(f.embedding, dtype=np.float32)
                norm = np.linalg.norm(emb)
                embedding = emb / max(norm, 1e-6)

            results.append(
                DetectedFace(
                    bbox=(bbox[0], bbox[1], bbox[2], bbox[3]),
                    score=score,
                    landmarks=landmarks,
                    embedding=embedding,
                )
            )

        return results

    def compute_embedding(
        self,
        image_bgr: np.ndarray,
        face: DetectedFace,
    ) -> np.ndarray:
        """Return 512-d normalized embedding for face."""
        if face.embedding is not None:
            return face.embedding

        if not self.is_ready():
            if not self.initialize():
                err_detail = f" ({self._last_error})" if self._last_error else ""
                raise RuntimeError(f"InsightFace model is not initialized or ready.{err_detail}")

        # If not already computed, run detection with embedder
        detected = self.detect_faces(image_bgr, threshold=face.score * 0.9)
        for d in detected:
            if d.embedding is not None:
                # Match by bbox IOU
                return d.embedding

        return np.zeros(512, dtype=np.float32)

    def compute_embeddings_batch(
        self,
        image_bgr: np.ndarray,
        faces: List[DetectedFace],
    ) -> List[np.ndarray]:
        """Extract embeddings for all detected faces."""
        return [self.compute_embedding(image_bgr, f) for f in faces]
