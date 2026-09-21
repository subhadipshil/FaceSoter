"""
Packaging and installer compilation automation script.
"""

from __future__ import annotations
import os
import sys
import subprocess
import shutil
import zipfile
from pathlib import Path


def find_iscc() -> Path | None:
    """Find Inno Setup Compiler executable."""
    # Check PATH
    iscc_path = shutil.which("ISCC") or shutil.which("iscc")
    if iscc_path:
        return Path(iscc_path)

    # Check common install locations
    common_paths = [
        Path(os.environ.get("ProgramFiles(x86)", "C:/Program Files (x86)")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "Inno Setup 6" / "ISCC.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
    ]
    for p in common_paths:
        if p.exists():
            return p
    return None


def build_pyinstaller():
    """Build standalone executable folder using PyInstaller."""
    root_dir = Path(__file__).resolve().parent.parent
    spec_file = root_dir / "FaceSoter.spec"

    print("=" * 70)
    print("Step 1: Building standalone bundle with PyInstaller...")
    print("=" * 70)

    cmd = [sys.executable, "-m", "PyInstaller", str(spec_file), "--noconfirm"]
    subprocess.check_call(cmd, cwd=str(root_dir))

    dist_app = root_dir / "dist" / "FaceSoter"
    if not dist_app.exists():
        raise RuntimeError(f"Build failed: {dist_app} does not exist.")
    print("PyInstaller build completed successfully.")
    return dist_app


def get_version(root_dir: Path) -> str:
    """Read version string from facesoter __init__.py."""
    init_file = root_dir / "src" / "facesoter" / "__init__.py"
    for line in init_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("__version__"):
            return line.split("=")[1].strip().strip('"').strip("'")
    return "1.1.0"


def build_portable_zip(dist_app: Path):
    """Build portable zip package."""
    root_dir = Path(__file__).resolve().parent.parent
    ver = get_version(root_dir)
    zip_path = root_dir / "dist" / f"FaceSoter-v{ver}-Portable.zip"

    print("=" * 70)
    print("Step 2: Creating Portable ZIP Package...")
    print(f"Destination: {zip_path}")
    print("=" * 70)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for file in dist_app.rglob("*"):
            rel = file.relative_to(dist_app)
            zf.write(file, arcname=str(Path("FaceSoter") / rel))

    print(f"Portable package created ({zip_path.stat().st_size / (1024*1024):.1f} MB).")
    return zip_path


def build_inno_setup():
    """Compile Inno Setup Windows installer."""
    root_dir = Path(__file__).resolve().parent.parent
    iss_file = root_dir / "installer" / "facesoter.iss"

    iscc = find_iscc()
    if not iscc:
        print("\nNotice: Inno Setup (ISCC.exe) not found on system. Skipping .exe installer.")
        print("To compile the installer, install Inno Setup 6 or run: winget install JRSoftware.InnoSetup")
        return None

    print("=" * 70)
    print("Step 3: Compiling Windows Installer (FaceSoter-Setup.exe)...")
    print("=" * 70)

    subprocess.check_call([str(iscc), str(iss_file)], cwd=str(root_dir / "installer"))
    setup_exe = root_dir / "dist" / "FaceSoter-Setup.exe"
    if setup_exe.exists():
        print(f"Windows installer created successfully: {setup_exe} ({setup_exe.stat().st_size / (1024*1024):.1f} MB)")
        return setup_exe
    return None


def main():
    dist_app = build_pyinstaller()
    build_portable_zip(dist_app)
    build_inno_setup()
    print("\n" + "=" * 70)
    print("Build Pipeline Finished Successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
