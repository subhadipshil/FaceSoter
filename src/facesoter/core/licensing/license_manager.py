"""
Licensing and Attribution Manager for FaceSoter.
"""

from pathlib import Path
from typing import Dict


class LicenseManager:
    """Manages loading and formatting third-party attribution and model terms."""

    @staticmethod
    def get_model_notice() -> str:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        notice_file = base_dir / "LICENSES" / "insightface-model-notice.txt"
        if notice_file.exists():
            return notice_file.read_text(encoding="utf-8")
        return "InsightFace buffalo_l is subject to non-commercial research terms."

    @staticmethod
    def get_third_party_notices() -> str:
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        notices_file = base_dir / "THIRD_PARTY_NOTICES.txt"
        if notices_file.exists():
            return notices_file.read_text(encoding="utf-8")
        return "Third-party notices file not found."

    @staticmethod
    def get_model_specifications() -> Dict[str, str]:
        return {
            "model_name": "buffalo_l",
            "version": "v0.7",
            "detector": "SCRFD-10GF (det_10g.onnx)",
            "recognizer": "ResNet50@WebFace600K / ArcFace (w600k_r50.onnx)",
            "landmarks_3d": "1k3d68.onnx",
            "landmarks_2d": "2d106det.onnx",
            "attribute": "genderage.onnx",
            "approx_size": "~326 MB",
            "download_source": "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip",
            "license_type": "Pre-trained models are for Non-Commercial Research Purposes Only (InsightFace). Source code is MIT.",
        }
