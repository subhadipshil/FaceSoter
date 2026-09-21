"""
Tests for UI assets resolution and donation dialog configuration.
"""

from __future__ import annotations
from pathlib import Path
from facesoter import __version__
from facesoter.ui.assets import get_asset_path
from facesoter.ui.dialogs.donate_dialog import UPI_ID


def test_version_bump():
    """Verify application version is 1.1.0."""
    assert __version__ == "1.1.0"


def test_asset_paths_resolution():
    """Verify essential bundled assets can be located."""
    icon_path = get_asset_path("icons/app_icon.ico")
    assert icon_path.exists(), f"App icon missing at {icon_path}"

    qr_path = get_asset_path("donate_qr.png")
    assert qr_path.exists(), f"UPI QR code image missing at {qr_path}"


def test_upi_id_correctness():
    """Verify UPI ID is set accurately."""
    assert UPI_ID == "subhadipshil.pnb@ybl"


def test_qr_asset_validity():
    """Verify the generated donate_qr.png is a valid PNG image file."""
    qr_path = get_asset_path("donate_qr.png")
    with open(qr_path, "rb") as f:
        header = f.read(8)
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    assert header == b"\x89PNG\r\n\x1a\n", "donate_qr.png is not a valid PNG file"
