# Changelog

All notable changes to **FaceSoter** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-10-13

### Added
- **Mode C: Single & Group Photo Separator**:
  - Automatically identifies face count per photo and separates solo portraits (`Single_Photos/`) from group/couple/family photos (`Group_Photos/`).
  * Automatic routing of photos with no detected faces to `No_Face/`.
  - Configurable destination subfolder names and minimum group face threshold (default: 2).
  - High-speed processing pipeline that skips face clustering/database lookup overhead for pure face count categorization.
  - Dedicated `SingleGroupView` UI and `SingleGroupReviewDialog` showing detailed metrics before file operations.
  - Sidebar navigation button and Home View Mode C card.
- **Fast Download Options & ZIP Installer for buffalo_l Models**:
  - Direct redirection button to open the official download link in external browser or download manager (IDM, FDM, Chrome) for maximum multi-threaded speed.
  - 1-click "Copy Download Link" button to copy direct archive URL to clipboard.
  - 1-click "Import Downloaded ZIP..." button that automatically verifies archive integrity, unpacks, and installs models without requiring manual extraction.
- **Auto-Closing Feature Announcement Poster**:
  - 3-second auto-close countdown with smooth animated timer progress bar.
  - Hover-pause intelligence: pausing countdown when user hovers to read comfortably.
  - 1-click "Try Feature Now 🚀" button transitioning directly to the new Single vs Group mode.
  - Suppress persistence via database setting `feature_poster_v12_shown` preventing nagging on subsequent launches.
  - "✨ What's New" button on Home View and Settings View to view feature highlights anytime.

## [1.1.0] - 2026-09-20

### Added
- **Application Icon Across Windows**:
  - Dedicated application icon embedded on Windows Taskbar using `SetCurrentProcessExplicitAppUserModelID`.
  - Window title bar and sidebar header branding with smooth-scaled logo icon and `v1.1` badge.
  - Safe runtime asset resolver (`facesoter.ui.assets.get_asset_path`) supporting both development and PyInstaller bundled runtime.
- **Fluent Obsidian Dark Theme**:
  - Polished modern dark aesthetic with obsidian `#121214` backdrop, `#0d0d0f` sidebar, and `#18181b` cards with 10px rounded corners.
  - Glowing accent state highlights (`#0284c7` / `#38bdf8`) and smooth hover feedback.
- **Subtle "Buy Me a Coffee" Feature**:
  - Integrated discreet UPI support for `subhadipshil.pnb@ybl`.
  - Scannable UPI QR code dialog supporting Google Pay, PhonePe, Paytm, and all UPI apps.
  - 1-click "Copy UPI ID" button with interactive feedback.
  - Non-intrusive placement in sidebar and About view without popups or nag screens.

### Fixed
- Fixed auto-initialization and execution provider fallbacks for InsightFace buffalo_l models.

## [1.0.0] - 2026-09-20

### Added
- **InsightFace Buffalo_L AI Integration**:
  - SCRFD-10GF face detector with 5-point landmark extraction.
  - ResNet50@WebFace600K ArcFace 512-d normalized embeddings.
  - Automatic download and integrity verification wizard with offline caching.
  - Advanced option for user-supplied existing model directories.
  - Model provider abstraction decoupling business logic from inference backend.
- **Mode A (Categorization)**:
  - Recursive directory scanner supporting JPG, JPEG, PNG, WEBP, BMP, TIFF, HEIC/HEIF.
  - Safe atomic file copy with EXIF metadata and timestamp preservation.
  - Intentional multi-person photo duplication across each matching person folder.
  - Automatic routing of non-face photos to `Uncategorized/No Face/`.
  - Graph/agglomerative clustering for unknown recurring faces into `Person 001`, `Person 002`, etc.
  - Pre-copy Review Dialog with representative thumbnails and folder renaming.
- **Mode B (Separation / Filter)**:
  - Target person selection and multi-target filtering.
  - Strict separation rule engine excluding matched photos from normal categorization outputs.
  - Interactive multi-face selector dialog when importing reference photos.
- **Persistence & Recovery**:
  - SQLite database with schema versioning and WAL mode.
  - Checkpoint tracking allowing paused or interrupted scans to resume from disk.
- **Modern Desktop UI**:
  - Native PySide6 dark-mode desktop interface.
  - Live progress monitoring with real files/sec throughput and ETA metrics.
- **Packaging & Delivery**:
  - PyInstaller configuration.
  - Inno Setup script compiling `FaceSoter-Setup.exe`.
  - Portable `.zip` build automation.
