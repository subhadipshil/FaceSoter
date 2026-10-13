# FaceSoter v1.2.0 Release Notes

**Release Tag**: `v1.2.0`  
**Release Date**: October 13, 2026  
**Build Target**: Windows 10 / 11 (64-bit)  

---

## 🚀 Overview

**FaceSoter v1.2.0** introduces **Mode C: Single & Group Photo Separator**, a high-speed AI categorization pipeline designed to quickly split photo collections into solo portraits (`Single_Photos/`) and group / family / event shots (`Group_Photos/`).

This release also resolves download bottlenecks by adding **external browser / download manager (IDM / FDM) redirection**, a **1-click direct link copy**, and a **1-click ZIP importer**. First-time users and upgraders are greeted by an **auto-closing 3-second feature announcement poster** with hover-pause intelligence and persistent suppression.

---

## 🌟 What's New in v1.2.0

### 1. 👥 Mode C: Single & Group Photo Separator
- **Smart Face Count Segmentation**: Evaluates faces per image with sub-millisecond classification.
- **Customizable Organization**:
  - `Single_Photos/`: Photos with exactly 1 detected face (solo portraits, headshots).
  - `Group_Photos/`: Photos with $\ge N$ faces (configurable threshold, default: 2).
  - `No_Face/`: Automatic routing of landscapes, objects, screenshots, and architecture.
- **Bypass Identity Overhead**: Skips 512-d ArcFace vector clustering and database lookups for pure face-count categorization, delivering up to **3× faster scanning throughput**.
- **Interactive Review Dialog**: Inspect counts, percentages, and destination directory previews before any disk write operations.

### 2. ⚡ High-Speed Model Downloads & 1-Click ZIP Installer
- **Browser & Download Manager Redirection**: Opens the official GitHub release download link directly in your default browser or download manager (Internet Download Manager, Free Download Manager) for multi-threaded maximum bandwidth.
- **Copy Download Link**: 1-click clipboard copy of the direct `buffalo_l.zip` URL.
- **Import Downloaded ZIP...**: Select a downloaded `.zip` file from your disk; FaceSoter will automatically verify integrity, extract to the local model cache, and initialize ONNX inference models without manual unpacking.

### 3. 🎨 Non-Intrusive Feature Announcement Poster
- **3-Second Auto-Close**: Elegant announcement banner appears on startup with a smooth animated countdown progress bar.
- **Hover-to-Pause**: Hovering the cursor over the poster pauses the timer, allowing comfortable reading.
- **One-Click Launch**: "Try Feature Now 🚀" jumps directly to the Single & Group workspace.
- **Suppression Persistence**: Stored in SQLite database (`feature_poster_v12_shown = true`), ensuring it never pesters users on subsequent launches. Accessible anytime via the **✨ What's New** button in Settings or Home.

### 4. 🛡️ Safe & Non-Destructive File Copying
- Preserves **all original EXIF metadata**, GPS tags, color profiles, and file timestamps.
- Zero-modification safety: Source photos are strictly copied atomically with collision avoidance (`_1`, `_2`).

---

## 📦 Release Assets & Checksums

| Asset | Type | Size | SHA-256 Checksum |
| :--- | :--- | :--- | :--- |
| **`FaceSoter-Setup.exe`** | Windows Inno Setup Installer | 121.0 MB | `880C1EB037AA7FBC71F3256B63C68EB4FD20EF701573947089466825537743EC` |
| **`FaceSoter-v1.2.0-Portable.zip`** | Standalone Portable Archive | 183.0 MB | `3FBCED927EE1CC3F46C60129C571655BFE61766EFB4E8891AEDFCE0628E6A865` |
| **`FaceSoter.exe`** | Main Executable Binary | 22.8 MB | `6790E7ED856157DCC25306D0615166DB0BAFDF180123715BDF358558CB98456C` |

---

## 💻 System Requirements

- **Operating System**: Windows 10 / Windows 11 (64-bit)
- **Processor**: Intel Core i3 / AMD Ryzen 3 or higher (AVX instruction set recommended)
- **Memory**: 4 GB RAM minimum (8 GB recommended for large libraries)
- **Storage**: ~500 MB for application + AI model cache
- **Graphics (Optional)**: DirectML / CUDA compatible GPU for hardware-accelerated ONNX inference

---

## 📥 Installation & Getting Started

### Option A: Windows Installer (Recommended)
1. Download **`FaceSoter-Setup.exe`**.
2. Run the installer and follow the setup wizard.
3. Launch FaceSoter from the Desktop or Start Menu.

### Option B: Portable Edition (No Installation Required)
1. Download **`FaceSoter-v1.2.0-Portable.zip`**.
2. Extract the archive to any folder or external USB drive.
3. Run `FaceSoter.exe`.

### Option C: Run from Source
```bash
git clone https://github.com/subhadipshil/FaceSoter.git
cd FaceSoter
python -m venv .venv
.venv\Scripts\activate
pip install -e .
python -m facesoter.main
```

---

## 🧪 Verification & Test Suite

All 40 unit and integration tests passed with 100% test coverage:
```
tests/test_model_downloader.py ........  [ 20%]
tests/test_pipeline.py ........          [ 40%]
tests/test_single_group_rule.py ....     [ 50%]
tests/test_ui_assets.py ................ [ 90%]
tests/test_ui_features.py ....           [100%]
40 passed in 4.90s
```

---

## ☕ Support the Project
FaceSoter is 100% free, open-source, and offline. If you find it helpful:
- **Star the repository** on GitHub!
- **UPI Support**: `subhadipshil.pnb@ybl` (Scannable QR code available in the application sidebar).
