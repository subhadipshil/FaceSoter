"""
Unit tests for ModelDownloader, SSL context generation, and model verification.
"""

import ssl
from pathlib import Path
from unittest.mock import patch, MagicMock
import urllib.error
import pytest

from facesoter.core.ai.model_downloader import (
    ModelDownloader,
    ModelVerificationError,
    EXPECTED_FILES,
)


def test_ssl_context_verified():
    """Verify that default SSL context creation works and enables verification."""
    ctx = ModelDownloader._get_ssl_context(verify=True)
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode != ssl.CERT_NONE


def test_ssl_context_unverified():
    """Verify that unverified SSL context creation disables hostname and cert verification."""
    ctx = ModelDownloader._get_ssl_context(verify=False)
    assert isinstance(ctx, ssl.SSLContext)
    assert ctx.verify_mode == ssl.CERT_NONE
    assert ctx.check_hostname is False


def test_verify_existing_nonexistent(tmp_path: Path):
    downloader = ModelDownloader(tmp_path)
    valid, msg = downloader.verify_existing(tmp_path / "nonexistent")
    assert not valid
    assert "does not exist" in msg.lower()


def test_verify_existing_missing_files(tmp_path: Path):
    downloader = ModelDownloader(tmp_path)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    valid, msg = downloader.verify_existing(model_dir)
    assert not valid
    assert "missing" in msg.lower()


def test_verify_existing_file_too_small(tmp_path: Path):
    downloader = ModelDownloader(tmp_path)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    # Create small dummy file
    (model_dir / "det_10g.onnx").write_bytes(b"dummy")
    (model_dir / "w600k_r50.onnx").write_bytes(b"dummy")

    valid, msg = downloader.verify_existing(model_dir)
    assert not valid
    assert "too small" in msg.lower()


def test_verify_existing_success(tmp_path: Path):
    downloader = ModelDownloader(tmp_path)
    model_dir = tmp_path / "models"
    model_dir.mkdir()
    for filename, min_size in EXPECTED_FILES.items():
        file_path = model_dir / filename
        with open(file_path, "wb") as f:
            f.seek(min_size + 1024)
            f.write(b"\0")

    valid, msg = downloader.verify_existing(model_dir)
    assert valid
    assert "valid and complete" in msg.lower()


def test_ssl_cert_error_fallback(tmp_path: Path):
    """Verify that CERTIFICATE_VERIFY_FAILED triggers fallback to unverified SSL context."""
    downloader = ModelDownloader(tmp_path)

    cert_error = urllib.error.URLError(
        "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1082)"
    )

    mock_response = MagicMock()
    mock_response.headers.get.return_value = "0"
    mock_response.read.side_effect = [b"", b""]  # immediate EOF to simulate empty stream
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    calls = []

    def mock_urlopen(req, timeout=30, context=None):
        calls.append(context)
        if len(calls) == 1:
            # First call fails with certificate error
            raise cert_error
        # Second call succeeds with fallback context
        return mock_response

    with patch("urllib.request.urlopen", side_effect=mock_urlopen):
        # We expect testzip or verification to raise ModelVerificationError because zip is empty,
        # but the key check is that urlopen was called twice, second time with unverified context
        try:
            downloader.download_and_install()
        except Exception:
            pass

    assert len(calls) == 2
    # First call was verified
    assert calls[0].verify_mode != ssl.CERT_NONE
    # Second call was unverified
    assert calls[1].verify_mode == ssl.CERT_NONE
