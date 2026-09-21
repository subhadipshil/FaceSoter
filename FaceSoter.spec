# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import sys
import os

block_cipher = None

src_dir = os.path.abspath("src")

datas = [
    ("THIRD_PARTY_NOTICES.txt", "."),
    ("LICENSES", "LICENSES"),
    ("assets", "assets"),
]
datas += collect_data_files("certifi")

hiddenimports = [
    "certifi",
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "onnxruntime",
    "cv2",
    "insightface",
    "insightface.app",
    "insightface.model_zoo",
    "PIL",
    "PIL.Image",
    "PIL.ImageOps",
    "sklearn",
    "sklearn.utils",
    "scipy",
    "scipy.spatial",
    "numpy",
]
hiddenimports += collect_submodules("facesoter")

a = Analysis(
    ["src/facesoter/app/main.py"],
    pathex=[src_dir, "."],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "matplotlib", "torch", "torchvision"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FaceSoter",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # Desktop GUI app, no console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/icons/app_icon.ico",
    version="installer/file_version_info.txt",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="FaceSoter",
)
