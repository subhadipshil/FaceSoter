# FaceSoter — Engineering Log & Progress Tracker

> **File Purpose**: Living technical log tracking architecture, database schemas, progress, execution milestones, verification, and debugging notes for FaceSoter. Updated continuously throughout development.

---

## 1. Project Overview & Specs
- **Application Name**: FaceSoter
- **Target OS**: Windows 10 / 11 (64-bit)
- **Primary Technology Stack**:
  - UI: PySide6 (Qt 6 for Python)
  - Core AI Engine: InsightFace `buffalo_l` (SCRFD-10GF face detection + ResNet50@WebFace600K ArcFace recognition)
  - Inference Runtime: ONNX Runtime (CPUExecutionProvider default fallback, CUDAExecutionProvider when available)
  - Storage & State: SQLite with ACID transactions, Write-Ahead Logging (WAL), and schema migration tracking
  - Packaging: PyInstaller + Inno Setup (`FaceSoter-Setup.exe`)
- **Key Modes**:
  - **Mode A (Categorization)**: Copies photos into person folders (e.g. `Categorized/Mom/`, `Categorized/Dad/`). Photos with multiple people are duplicated into **every** matching person folder. Non-face photos go to `Uncategorized/No Face/`. Recurring unknown faces are clustered into `Person 001`, `Person 002`, etc.
  - **Mode B (Separation / Filter)**: Scans source photos for selected target person profiles. Matched photos are copied into `SeparateFilter/<TargetName>/` and **strictly excluded** from normal categorization outputs.

---

## 2. Completed Implementations

### A. Core Settings & Configuration (`src/facesoter/core/settings/config.py`)
- Standard AppData resolution (`%LOCALAPPDATA%/FaceSoter`)
- Managed subdirectories: `models/`, `thumbnails/`, `logs/`, `facesoter.db`
- `AppConfig` dataclass and `ConfigManager` JSON disk persistence
- Configurable AI thresholds (detector confidence, recognition similarity, clustering similarity, min face size)
- Configurable file collision policies (`rename_numbered`, `skip`, `overwrite`)

### B. Structured Logging (`src/facesoter/core/logging/logger.py`)
- Rotating file handlers (`facesoter.log` max 10MB x 5 backups, `error.log` max 5MB x 3 backups)
- Console stream handler with timestamp, level, and thread name
- Zero image content leakage into logs

### C. SQLite Persistence Layer (`src/facesoter/core/database/`)
- Schema migrations version 1 (`schema.py`)
- Connection manager with WAL mode, foreign keys, synchronous NORMAL, and transaction context manager (`db_manager.py`)
- Repositories:
  - `PersonRepository`: CRUD for enrolled profiles, reference face embeddings, profile merging
  - `ImageRepository`: scanned images, detected faces, bounding boxes, landmarks, 512-d embeddings
  - `JobRepository`: job lifecycle, batch file queues, classification results, checkpoint resumption, failed files
  - `SettingsRepository`: key-value app settings and model registry

### D. Licensing & Attribution (`src/facesoter/core/licensing/`, `LICENSES/`, `THIRD_PARTY_NOTICES.txt`)
- `LICENSES/insightface-model-notice.txt`: Explicit acknowledgment of SCRFD / ArcFace / InsightFace authors and clear statement that pretrained weights are strictly for **non-commercial research purposes only**.
- `THIRD_PARTY_NOTICES.txt`: Full third-party licenses for PySide6, ONNX Runtime, OpenCV, NumPy, SciPy, Scikit-Learn, Pillow, Pillow-Heif, PyInstaller.
- `LicenseManager`: Helper class providing attribution text to UI.

### E. AI Layer & Model Management (`src/facesoter/core/ai/`)
- `provider.py`: Clean abstract interfaces `FaceDetectionProvider`, `FaceEmbeddingProvider`, `FaceModelProvider`
- `model_downloader.py`: Official `buffalo_l.zip` downloader with progress callbacks, cancellation, zip integrity validation, and local folder installation
- `insightface_provider.py`: Concrete `buffalo_l` provider using SCRFD-10GF and ResNet50@WebFace600K ArcFace
- `matcher.py`: Cosine similarity calculation, multi-reference aggregation (`max` and `top3_avg`), threshold matching
- `clusterer.py`: Cosine-distance agglomerative / graph clustering of unknown faces into `Person 001`, `Person 002`, with representative medoid face selection

### F. File Processing & Organizer Engine (`src/facesoter/core/scanner/`, `src/facesoter/core/organizer/`)
- `image_reader.py`: EXIF orientation correction in memory (never alters original file), format support (`.jpg`, `.jpeg`, `.png`, `.webp`, `.bmp`, `.tiff`, `.heic`, `.heif`), SHA-256 hashing
- `thumbnail_cache.py`: High-speed disk cache for face crop portraits with 20% margin
- `file_scanner.py`: Recursive or flat file scanner with cancel check
- `file_copier.py`: Safe atomic copy (copy to temp file in destination directory -> fsync -> atomic replace), EXIF and timestamp preservation, numbered collision renaming (`_1.jpg`)
- `rule_engine.py`: Mode A multi-face duplication and no-face routing; Mode B target filtering with strict categorization exclusion
- `engine.py`: Pre-copy summary breakdown generator and atomic copy batch executor

### G. Job Pipeline & Background Workers (`src/facesoter/core/jobs/`)
- `pipeline.py`: End-to-end pipeline: Discovery -> Bounded-Memory Batch Detection -> Matching -> Clustering -> Organization Planning
- `worker.py`: Cooperative background worker thread with `pause()`, `resume()`, and `cancel()`
- `job_manager.py`: Coordinator for job creation, checkpoint resume, and worker lifecycle

### H. Native Desktop UI (`src/facesoter/ui/`)
- `styles/theme.py`: Polished Windows dark-mode desktop theme and QSS
- `widgets/progress_panel.py`: Live progress panel with speed, counts, progress bar, pause/resume/cancel
- `widgets/thumbnail_card.py`: Face thumbnail card with photo count and inline rename button
- `dialogs/model_setup_dialog.py`: Model download wizard with real download progress, verification, and custom folder picker
- `dialogs/face_picker_dialog.py`: Interactive face selector when importing multi-face reference photos
- `dialogs/review_dialog.py`: Pre-copy review dialog showing detected clusters and destination folder tree preview
- `dialogs/failed_files_dialog.py`: Failed files inspector with text log exporter
- `views/home_view.py`: Overview, mode action cards, model status banner, recent jobs table
- `views/organize_view.py`: Mode A Categorization view with folder pickers, progress panel, review trigger, copy execution
- `views/separation_view.py`: Mode B Separation view with target people checkboxes, reference import, strict exclusion rule
- `views/people_view.py`: Person profiles manager with gallery, add photo, merge profiles
- `views/jobs_view.py`: Job history table with resume and view failed files actions
- `views/settings_view.py`: AI thresholds, file copy rules, hardware options, directory paths
- `views/about_view.py`: About dialog with model terms, third-party licenses, and 100% local privacy guarantee
- `main_window.py`: Primary desktop window with sidebar navigation, status bar, and startup model check
- `app/application.py` & `app/main.py`: Application lifecycle bootstrap
- `run.py`: Convenient root launcher

### I. Automated Tests (`tests/`)
- `test_database.py`: Schema migrations, PersonRepository CRUD, ImageRepository, JobRepository, crash recovery
- `test_matcher.py`: Cosine similarity, multi-reference aggregation, threshold decision
- `test_clusterer.py`: Grouping unknown embeddings into distinct clusters, medoid representative face
- `test_file_copier.py`: Atomic write, collision numbering, hash duplicate skipping, original file integrity
- `test_rule_engine.py`: Acceptance Test A (multi-person duplication + no-face routing) & Acceptance Test B (Separation filter + strict exclusion)
- `test_pipeline.py`: Full end-to-end integration test of pipeline and organizer

### J. Packaging & Documentation
- `assets/icons/app_icon.ico` & `assets/logo.png`: Application branding
- `FaceSoter.spec`: PyInstaller standalone bundle configuration
- `installer/facesoter.iss`: Inno Setup installer script compiling `FaceSoter-Setup.exe`
- `installer/build_installer.py`: Build automation script
- `README.md`, `BUILD.md`, `CHANGELOG.md`, `requirements.txt`

---

## 3. Work Log & Execution Updates
- [2026-09-20 15:43] Plan approved by user.
- [2026-09-20 15:44] Dependencies installation launched into `.venv`.
- [2026-09-20 15:45] Core configuration, logging, database schema, migrations, and repositories implemented.
- [2026-09-20 15:46] Model notices, licensing files, and license manager implemented.
- [2026-09-20 15:47] AI provider interfaces, model downloader, matcher, clusterer, and image scanner created.
- [2026-09-20 15:48] File copier, rule engine, organizer engine, and scan pipeline created.
- [2026-09-20 15:49] Worker thread and job manager created.
- [2026-09-20 15:50] UI theme, progress panel, thumbnail card, and dialogs created.
- [2026-09-20 15:51] All 7 UI views implemented (Home, Organize, Separation, People, Jobs, Settings, About).
- [2026-09-20 15:52] MainWindow and application bootstrap created.
- [2026-09-20 15:53] Test suite implemented (`test_database.py`, `test_matcher.py`, `test_clusterer.py`, `test_file_copier.py`, `test_rule_engine.py`, `test_pipeline.py`).
- [2026-09-20 15:54] Application icons generated, packaging scripts created (`FaceSoter.spec`, `facesoter.iss`, `build_installer.py`), and documentation completed (`README.md`, `BUILD.md`, `CHANGELOG.md`, `requirements.txt`).
- [2026-09-20 18:50] UI beautification with Obsidian Dark palette, Windows Taskbar AppUserModelID icon integration, and subtle Buy Me a Coffee UPI QR code modal.
- [2026-09-20 19:10] Version bumped to v1.1.0 across all components; automated tests verified (29/29 passing) and release binaries recompiled (`FaceSoter-Setup.exe` & `FaceSoter-v1.1.0-Portable.zip`).
