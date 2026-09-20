"""
Face AI core package.
"""

from facesoter.core.ai.provider import (
    FaceModelProvider,
    FaceDetectionProvider,
    FaceEmbeddingProvider,
    DetectedFace,
)
from facesoter.core.ai.matcher import FaceMatcher
from facesoter.core.ai.clusterer import FaceClusterer, FaceCluster
from facesoter.core.ai.model_downloader import ModelDownloader, ModelVerificationError
from facesoter.core.ai.insightface_provider import InsightFaceBuffaloLProvider

__all__ = [
    "FaceModelProvider",
    "FaceDetectionProvider",
    "FaceEmbeddingProvider",
    "DetectedFace",
    "FaceMatcher",
    "FaceClusterer",
    "FaceCluster",
    "ModelDownloader",
    "ModelVerificationError",
    "InsightFaceBuffaloLProvider",
]
