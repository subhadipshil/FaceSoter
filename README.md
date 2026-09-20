# FaceSoter — Windows Desktop Face-Based Photo Organizer

<div align="center">

![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-blue.svg?style=flat-square&logo=windows)
![Python](https://img.shields.io/badge/Python-3.10%20--%203.14-blue.svg?style=flat-square&logo=python)
![GUI](https://img.shields.io/badge/GUI-PySide6%20(Qt6)-41cd52.svg?style=flat-square&logo=qt)
![Inference](https://img.shields.io/badge/Inference-ONNX%20Runtime-orange.svg?style=flat-square)
![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local%20Inference-brightgreen.svg?style=flat-square)
![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)

**A high-performance, local-first Windows desktop application for organizing personal photo libraries of any size (from hundreds to 100,000+ photos) strictly by human face presence and identity.**

</div>

---

## Overview

Unlike generic photo managers that organize by scenery, pets, or arbitrary image tags, **FaceSoter** focuses exclusively on human identity. Every face detection, embedding comparison, and clustering operation runs **100% offline and locally on your computer** using ONNX Runtime. No photos, face crops, or personal data ever leave your machine.

---

## Key Features

### 1. Dual Organization Modes

```
                                  [Source Photos]
                                         │
                 ┌───────────────────────┴───────────────────────┐
                 ▼                                               ▼
     [Mode A: Categorization]                        [Mode B: Separation / Filter]
   • Sorts entire collection into                  • Select target people (e.g. Mom, Dad)
     person folders                                • Isolates only matching photos
   • Duplicates multi-person photos                • Strict exclusion: isolated photos
   • Clusters unknown recurring faces                are kept out of general folders
   • Non-faces -> Uncategorized/No Face
```

* **Mode A: Categorization**
  * Sorts your entire photo collection into person folders (`Categorized/Mom/`, `Categorized/Dad/`).
  * **Intentional Duplication for Multi-Person Photos**: If a photo contains Mom, Dad, and your friend, it is safely copied into **every** matching person's folder so no memory is missing.
  * **No Face Routing**: Photos without human faces (landscapes, screenshots, documents, objects) go cleanly to `Uncategorized/No Face/`.
  * **Automatic Unknown Face Clustering**: Unenrolled recurring faces are grouped into `Person 001/`, `Person 002/` with thumbnail previews and one-click renaming.

* **Mode B: Targeted Separation / Filter**
  * Choose one or more target people (e.g., Mom).
  * Isolates only photos containing that target person into `SeparateFilter/Mom/`.
  * **Strict Separation Rule**: Those photos are strictly excluded from general folders.

---

### 2. Deep Learning Face Engine (InsightFace Buffalo_L)

* **Face Detector**: **SCRFD-10GF** (`det_10g.onnx`) — state-of-the-art fast face detection with 5-point landmark alignment.
* **Feature Extractor**: **ResNet50@WebFace600K ArcFace** (`w600k_r50.onnx`) — produces 512-dimensional normalized face embeddings.
* **Automated Model Setup**: Built-in wizard downloads and verifies the official model weights on first run, with support for corporate proxies, custom CA stores, and offline local model folders.
* **Hardware Acceleration**: Automatic GPU acceleration via ONNX Runtime CUDA execution provider with automatic CPU fallback.

---

### 3. Data Integrity & Non-Destructive Safety

* **Non-Destructive Copy**: Your original source photos are never moved, renamed, or modified.
* **EXIF & Timestamp Preservation**: Preserves original camera EXIF metadata, orientation, and file creation/modification dates.
* **Collision Safety**: Prevents file overwrites by appending numeric suffixes (`_1.jpg`) and skips duplicate content using SHA-256 hash checks.
* **ACID Crash Recovery**: Uses a SQLite database transaction log. If interrupted by a power cut or restart, scanning resumes seamlessly without duplicate work.

---

## Output Folder Structure

### Mode A: Categorization
```text
ExportFolder/
├── Categorized/
│   ├── Mom/
│   │   ├── IMG_0001.jpg
│   │   └── IMG_0024.jpg
│   ├── Dad/
│   │   ├── IMG_0001.jpg       <- Multi-person photo safely duplicated into Dad's folder
│   │   └── IMG_0088.jpg
│   ├── Person 001/            <- Automatically clustered unknown person
│   │   └── IMG_0150.jpg
│   └── Person 002/
│       └── IMG_0210.jpg
└── Uncategorized/
    └── No Face/               <- Photos with 0 detectable human faces
        ├── Landscape_sunset.jpg
        └── Receipt_doc.jpg
```

### Mode B: Separation / Filter
```text
ExportFolder/
└── SeparateFilter/
    ├── Mom/
    │   ├── IMG_0001.jpg
    │   └── IMG_0512.jpg
    └── Dad/
        ├── IMG_0001.jpg
        └── IMG_0740.jpg
```

---

## System Requirements

| Component | Minimum | Recommended |
| :--- | :--- | :--- |
| **Operating System** | Windows 10 (64-bit) | Windows 11 (64-bit) |
| **CPU** | Intel Core i3 / AMD Ryzen 3 | Intel Core i5/i7 / AMD Ryzen 5/7 |
| **RAM** | 4 GB | 8 GB or more (for 50,000+ photo collections) |
| **Storage** | 500 MB free for app & model | Fast NVMe / SSD for photo export |
| **GPU (Optional)** | None (CPU inference supported) | NVIDIA GTX/RTX GPU with CUDA |

---

## Installation & Quick Start

### 1. Windows Setup Installer (Recommended)
1. Download **`FaceSoter-Setup.exe`** from [Releases](https://github.com/subhadipshil/FaceSoter/releases).
2. Run the installer and launch **FaceSoter**.
3. On first run, the **Model Setup** dialog will appear. Click **Download & Install** to retrieve the official `buffalo_l` model package (~326 MB).
4. Once verification passes, you are ready to organize photos!

### 2. Portable Archive
1. Download and extract **`FaceSoter-v1.0.0-Portable.zip`**.
2. Run `FaceSoter.exe` directly without installing.

---

## User Guide

### Enrolling People & Reference Photos
1. Open **People & Profiles** in the sidebar.
2. Click **Add Person** and enter a name (e.g. `Mom`).
3. Click **Add Reference Photo...** and select a clear portrait photo. If the photo contains multiple people, an interactive selector will prompt you to pick the correct face.
4. Adding 2–3 reference photos across different angles and lighting conditions maximizes recognition accuracy.

### Running Mode A (Categorize Photos)
1. Click **Categorize Photos** in the sidebar.
2. Select your **Source Folder** and **Export Folder**.
3. Check **Include subfolders (recursive scan)** if your photos are in nested subdirectories.
4. Click **Start Categorization Scan**.
5. Once scanning finishes, review the detected clusters and rename `Person 001`, `Person 002`, etc., if desired.
6. Click **Start Organization (Copy Files)** to copy your organized photos.

### Running Mode B (Separate / Filter)
1. Click **Separate / Filter** in the sidebar.
2. Select your **Source Folder** and **Export Folder**.
3. Check the target person profiles you want to filter out.
4. Click **Start Separation Scan**. Matching photos will be isolated into their dedicated folders.

---

## Development Setup

### Running from Source
```powershell
# 1. Clone repository
git clone https://github.com/subhadipshil/FaceSoter.git
cd FaceSoter

# 2. Create virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run application
python run.py
```

### Running Automated Tests
```powershell
pytest tests/ -v
```

### Building Executable & Installer
See [BUILD.md](file:///c:/Users/subha/Documents/GitHub/FaceSoter/BUILD.md) for full details:
```powershell
# Build standalone PyInstaller executable & Inno Setup installer
python installer/build_installer.py
```

---

## Troubleshooting

| Issue | Cause | Solution |
| :--- | :--- | :--- |
| **Model Download: SSL Certificate Verify Failed** | Corporate proxy, antivirus SSL inspection, or outdated root certificates | Resolved automatically via `certifi` CA fallback. You can also manually download `buffalo_l.zip` and select **Use Existing Model Folder...**. |
| **"Model detection failed: InsightFace model is not initialized"** | Model was downloaded but not yet loaded into memory | Fixed in latest release with automatic lazy-loading and background pre-warming. |
| **Photos in portrait/vertical orientation missed** | Image EXIF orientation mismatch | FaceSoter automatically parses EXIF rotation tags in memory during inference without modifying original files. |
| **Too many unknown person clusters** | High clustering similarity threshold | Navigate to **Settings** -> **AI Parameters** and adjust the **Clustering Threshold** (e.g. from `0.55` down to `0.50`). |

---

## Model Licensing & Attributions

* **Model Architecture**: InsightFace `buffalo_l` (SCRFD-10GF detection + ResNet50@WebFace600K ArcFace recognition).
* **Attribution**: DeepInsight & InsightFace team (Jiankang Deng, Jia Guo, Niannan Xue, Alexandros Lattas, Stefanos Zafeiriou).
* **License Terms**: While FaceSoter application code is licensed under the **MIT License**, the InsightFace pre-trained models are provided strictly for **non-commercial research purposes**.
* For full legal notices, see [THIRD_PARTY_NOTICES.txt](file:///c:/Users/subha/Documents/GitHub/FaceSoter/THIRD_PARTY_NOTICES.txt) and [LICENSES/](file:///c:/Users/subha/Documents/GitHub/FaceSoter/LICENSES/).
