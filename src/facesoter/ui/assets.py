"""
Asset locator for icons, logos, and UI resources.
"""

from __future__ import annotations
import sys
from pathlib import Path


def get_asset_path(relative_name: str) -> Path:
    """
    Locate an asset file robustly across both local Python development
    and PyInstaller frozen standalone binaries.
    """
    # 1. PyInstaller temporary extraction folder
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        candidate = Path(sys._MEIPASS) / "assets" / relative_name
        if candidate.exists():
            return candidate
        candidate_alt = Path(sys._MEIPASS) / relative_name
        if candidate_alt.exists():
            return candidate_alt

    # 2. Next to running executable (installed directory)
    exe_dir = Path(sys.executable).parent
    candidate_exe = exe_dir / "assets" / relative_name
    if candidate_exe.exists():
        return candidate_exe
    candidate_internal = exe_dir / "_internal" / "assets" / relative_name
    if candidate_internal.exists():
        return candidate_internal

    # 3. Source repository root (src/facesoter/ui/assets.py -> FaceSoter root)
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    candidate_repo = repo_root / "assets" / relative_name
    if candidate_repo.exists():
        return candidate_repo

    return repo_root / "assets" / relative_name
