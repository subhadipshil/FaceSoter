# FaceSoter — Developer Build & Packaging Guide

This document explains how to set up the development environment, execute tests, and build both the standalone Windows binary and installer.

---

## 1. Development Setup

### Prerequisites
* **Windows 10 or 11 (64-bit)**
* **Python 3.10+ (tested on Python 3.10 through 3.14)**
* **Git**
* *(Optional for installer)* **Inno Setup 6**: install via `winget install JRSoftware.InnoSetup`

### Environment Installation
Clone the repository and create a virtual environment:
```powershell
git clone https://github.com/subhadipshil/FaceSoter.git
cd FaceSoter

python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

---

## 2. Running from Source

Run the desktop application directly:
```powershell
python run.py
```

Or execute as a module:
```powershell
$env:PYTHONPATH = "$PWD\src"
python -m facesoter.app.main
```

---

## 3. Running Automated Tests

FaceSoter includes a comprehensive test suite covering AI abstractions, matching, clustering, rule engines, persistence, and file operations:

```powershell
.\.venv\Scripts\pytest tests/ -v
```

To run individual test modules:
```powershell
.\.venv\Scripts\pytest tests/test_rule_engine.py -v
.\.venv\Scripts\pytest tests/test_clusterer.py -v
.\.venv\Scripts\pytest tests/test_database.py -v
.\.venv\Scripts\pytest tests/test_file_copier.py -v
```

---

## 4. Production Packaging

### Building Standalone Executable
Compile the application with PyInstaller:
```powershell
.\.venv\Scripts\pyinstaller FaceSoter.spec --noconfirm
```
The output directory will be created at:
`dist/FaceSoter/FaceSoter.exe`

### Building the Windows Installer (`FaceSoter-Setup.exe`)
Ensure Inno Setup is installed, then run the automated packaging script:
```powershell
python installer/build_installer.py
```
This generates:
1. `dist/FaceSoter/FaceSoter.exe` (Standalone bundle)
2. `dist/FaceSoter-v1.1.0-Portable.zip` (Portable archive)
3. `dist/FaceSoter-Setup.exe` (Official Windows setup installer)
