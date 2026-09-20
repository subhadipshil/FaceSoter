# Changelog

All notable changes to **FaceSoter** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
