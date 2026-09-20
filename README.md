# FaceSoter — Windows Desktop Face-Based Photo Organizer

**FaceSoter** is a production-grade, local-first Windows desktop application for organizing large personal photo collections (from thousands to 100,000+ photos) based strictly on the presence and identity of human faces.

Unlike generic gallery tools that classify scenery, food, or pets, FaceSoter focuses exclusively on human identity. Photos are organized into person folders or isolated using targeted separation filters, with all AI inference executed 100% locally on your machine.

---

## Key Features

### 1. Dual Processing Modes
* **Mode A: Categorization**
  * Sorts your entire photo collection into person folders (e.g. `Categorized/Mom/`, `Categorized/Dad/`).
  * **Intentional Duplication for Multi-Person Photos**: If a photo contains Mom, Dad, and Dhruv, the original image is safely copied into **every** matching person's folder.
  * **No Face Routing**: Photos without any detectable human face (landscapes, screenshots, documents, food) are routed to `Uncategorized/No Face/`.
  * **Automatic Unknown Face Clustering**: Faces of recurring unknown people are grouped using embedding similarity into `Person 001/`, `Person 002/`, etc., with representative face thumbnails and inline renaming before copying.
* **Mode B: Separation / Filter**
  * Select one or more target person profiles (e.g., Mom and Dad).
  * Scans all photos and isolates matching images into `SeparateFilter/Mom/` and `SeparateFilter/Dad/`.
  * **Strict Separation Rule**: Any photo matching a filtered target is strictly excluded from normal person folders and No Face folders.

### 2. Core AI Model: InsightFace Buffalo_L
* **Detector**: SCRFD-10GF (`det_10g.onnx`) for high-precision face detection and 5-point facial landmarks.
* **Recognizer**: ResNet50@WebFace600K ArcFace (`w600k_r50.onnx`) generating 512-dimensional normalized face embeddings.
* **Automatic Model Setup**: On first launch, the official model package (~326 MB) is fetched directly from the upstream InsightFace repository and cached locally.
* **Custom Model Folder**: Advanced users can point to an existing local folder containing compatible ONNX models.
* **Hardware Acceleration**: Automatic negotiation for NVIDIA GPUs via ONNX Runtime `CUDAExecutionProvider` with rock-solid fallback to `CPUExecutionProvider`.

### 3. Safety, Integrity & Recovery
* **Non-Destructive**: Original files are never modified, deleted, or recompressed.
* **EXIF & Timestamp Preservation**: Preserves original image orientation, camera metadata, and timestamps during atomic copy.
* **Collision-Safe File Copying**: Prevents accidental overwrites by appending numbers (`_1.jpg`) for files with different content, and detecting true duplicates using SHA-256 content hashes.
* **Crash Recovery & Checkpointing**: Scans are tracked in an ACID SQLite database. If a scan of 100,000 photos is paused or interrupted by a system reboot, it resumes from the exact file boundary.

### 4. 100% Local & Privacy-Preserving
* All face detection, alignment, embedding extraction, and clustering happen entirely on your computer.
* No photos, face crops, or embeddings are ever uploaded to cloud services.
* External network access is used solely on first run to download model weights from the official repository.

---

## System Requirements
* **Operating System**: Windows 10 or Windows 11 (64-bit)
* **Processor**: Intel Core i3 / AMD Ryzen 3 or higher
* **Memory (RAM)**: 4 GB minimum (8 GB recommended for 50,000+ photo libraries)
* **Disk Space**: ~500 MB for application and model weights, plus space for copied photos
* **GPU (Optional)**: NVIDIA GeForce GTX/RTX GPU with CUDA support for accelerated batch inference

---

## Installation

### Standard Windows Installer
1. Download `FaceSoter-Setup.exe` from releases.
2. Run the installer and follow the setup wizard.
3. Launch **FaceSoter** from your Start Menu or Desktop.
4. On first launch, the **Model Setup** dialog will appear. Click **Download & Install** to fetch the official `buffalo_l` model package (~326 MB). Once verification passes, you are ready to organize!

### Portable Version
1. Download and extract `FaceSoter-v1.0.0-Portable.zip`.
2. Run `FaceSoter.exe`.

---

## How to Use

### Mode A: Categorizing Your Photo Library
1. Launch FaceSoter and click **Mode A: Categorize Photos**.
2. Select your **Source Folder** (e.g. `D:\Photos`).
3. Select your **Export Folder** (e.g. `E:\OrganizedPhotos`).
4. Ensure **Include subfolders** is checked if your source collection contains subdirectories.
5. Click **Start Categorization Scan**.
6. When scanning finishes, the **Review Dialog** will appear:
   * Review detected people clusters (`Person 001`, `Person 002`, etc.) and click **Rename** to provide real names (e.g. `Uncle Joe`).
   * Inspect the planned folder tree and total copy count.
7. Click **Start Organization (Copy Files)**. FaceSoter will safely copy your images into the designated folders.

### Mode B: Separating Photos of Specific People
1. Click **Mode B: Separate / Filter**.
2. Select your **Source Folder** and **Export Folder**.
3. Under **Select Target People to Filter**, check the boxes next to the people you wish to isolate (e.g. `[x] Mom`).
   * If the person is not yet enrolled, click **Import New Reference Photo...** to add them. If the photo has multiple people, an interactive selector will prompt you to choose the target face.
4. Click **Start Separation Scan**.
5. All matching photos are copied to `ExportFolder/SeparateFilter/<TargetName>/` and excluded from normal categorized folders.

### Managing Person Profiles
1. Navigate to **People & Profiles** in the sidebar.
2. Click **Add Person** to create a profile.
3. Select a profile and click **Add Reference Photo...** to enroll photos of that person. Multiple reference photos per person improve recognition across angles and lighting.
4. If two profiles belong to the same person, use **Merge with Another...** to combine them.

---

## Output Directory Structure

### Categorization Output Example
```
ExportFolder/
├── Categorized/
│   ├── Mom/
│   │   ├── IMG_0001.jpg
│   │   └── IMG_0024.jpg
│   ├── Dad/
│   │   ├── IMG_0001.jpg       <- Multi-person photo duplicated into Dad's folder
│   │   └── IMG_0088.jpg
│   ├── Person 001/            <- Automatically clustered recurring unknown person
│   │   └── IMG_0150.jpg
│   └── Person 002/
│       └── IMG_0210.jpg
└── Uncategorized/
    └── No Face/               <- Photos with 0 detectable human faces
        ├── Screenshot_12.png
        ├── Landscape_sunset.jpg
        └── Receipt_doc.jpg
```

### Separation Output Example
```
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

## Troubleshooting

| Problem | Cause | Solution |
| :--- | :--- | :--- |
| **Model Setup reports "Download Failed"** | Network connectivity issue or GitHub rate limit | Click **Retry** or download `buffalo_l.zip` in your browser from the official URL and click **Use Existing Model Folder...** |
| **Faces in rotated photos missed** | Image EXIF orientation flag | FaceSoter automatically corrects EXIF rotation in memory during inference without altering the source file. |
| **Too many unknown person clusters** | Clustering threshold is too strict | Go to **Settings** -> **AI Parameters** and adjust the **Clustering Threshold** (e.g. lower from 0.55 to 0.50). |
| **Non-faces detected as people** | Detector threshold too low | Increase **Detector Confidence Threshold** in Settings (e.g. from 0.50 to 0.60). |

---

## Pre-Trained Model License & Attributions
* **Model**: InsightFace `buffalo_l` (SCRFD-10GF + ResNet50@WebFace600K ArcFace)
* **Attribution**: DeepInsight & InsightFace contributors (Jiankang Deng, Jia Guo, Niannan Xue, Alexandros Lattas, Stefanos Zafeiriou).
* **Terms of Use**: While the InsightFace source code is MIT licensed, the official pre-trained model weights are provided strictly for **non-commercial research purposes only**.
* See [THIRD_PARTY_NOTICES.txt](file:///c:/Users/subha/Documents/GitHub/FaceSoter/THIRD_PARTY_NOTICES.txt) and [LICENSES/insightface-model-notice.txt](file:///c:/Users/subha/Documents/GitHub/FaceSoter/LICENSES/insightface-model-notice.txt) for full notices.
