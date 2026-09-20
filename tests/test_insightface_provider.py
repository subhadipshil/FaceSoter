"""
Unit tests for InsightFaceBuffaloLProvider path resolution and auto-initialization.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch
import numpy as np
import pytest

from facesoter.core.ai.insightface_provider import InsightFaceBuffaloLProvider


def test_provider_initial_state(tmp_path: Path):
    provider = InsightFaceBuffaloLProvider(tmp_path)
    assert not provider.is_ready()
    info = provider.get_info()
    assert info["name"] == "buffalo_l"
    assert not info["ready"]


def test_provider_missing_model_error(tmp_path: Path):
    provider = InsightFaceBuffaloLProvider(tmp_path)
    # Trying to initialize with empty models directory
    ok = provider.initialize()
    assert not ok
    assert not provider.is_ready()
    assert "det_10g.onnx" in provider._last_error


def test_detect_faces_auto_initializes(tmp_path: Path):
    provider = InsightFaceBuffaloLProvider(tmp_path)

    # Mock initialize to return True and set mock _app
    mock_app = MagicMock()
    mock_face = MagicMock()
    mock_face.det_score = 0.95
    mock_face.bbox = [10, 10, 50, 50]
    mock_face.kps = None
    mock_face.normed_embedding = np.ones(512, dtype=np.float32)
    mock_app.get.return_value = [mock_face]

    def fake_initialize(use_gpu=False):
        provider._app = mock_app
        provider._is_ready = True
        return True

    with patch.object(provider, "initialize", side_effect=fake_initialize):
        dummy_img = np.zeros((100, 100, 3), dtype=np.uint8)
        faces = provider.detect_faces(dummy_img)
        assert len(faces) == 1
        assert faces[0].score == 0.95
        assert provider.is_ready()
