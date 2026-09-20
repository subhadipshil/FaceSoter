"""
Model downloader and verifier for official InsightFace buffalo_l package.
"""

from __future__ import annotations
import os
import sys
import time
import zipfile
import shutil
import urllib.request
import urllib.error
import ssl
import threading
from pathlib import Path
from typing import Callable, Optional, Tuple, Dict, Any
from facesoter.core.logging.logger import get_logger

logger = get_logger("model_downloader")

OFFICIAL_BUFFALO_L_URL = "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
EXPECTED_FILES = {
    "det_10g.onnx": 10 * 1024 * 1024,      # ~16 MB minimum
    "w600k_r50.onnx": 150 * 1024 * 1024,   # ~240 MB minimum
}
OPTIONAL_FILES = ["1k3d68.onnx", "2d106det.onnx", "genderage.onnx"]


class ModelVerificationError(Exception):
    """Raised when model files fail validation."""
    pass


class ModelDownloader:
    """Handles downloading, extracting, and verifying the official buffalo_l model."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.model_dir = target_dir / "buffalo_l"
        self._cancel_event = threading.Event()
        self._is_downloading = False

    @property
    def is_installed(self) -> bool:
        """Check if required model files exist and have non-zero size."""
        return self.verify_existing(self.model_dir)[0]

    def verify_existing(self, directory: Path) -> Tuple[bool, str]:
        """Verify if a directory contains a valid buffalo_l model package."""
        if not directory.exists() or not directory.is_dir():
            return False, f"Directory does not exist: {directory}"

        for filename, min_size in EXPECTED_FILES.items():
            file_path = directory / filename
            if not file_path.exists():
                return False, f"Missing required model file: {filename}"
            actual_size = file_path.stat().st_size
            if actual_size < min_size:
                return False, f"File {filename} is too small ({actual_size} bytes, expected > {min_size})"

        return True, "Model package is valid and complete."

    @staticmethod
    def _get_ssl_context(verify: bool = True) -> ssl.SSLContext:
        """
        Create a resilient SSL context.
        Attempts to load certifi CA bundle and platform root certificates.
        If verify is False (fallback mode), returns an unverified context.
        """
        if not verify:
            try:
                return ssl._create_unverified_context()
            except AttributeError:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                return ctx

        ctx = None
        # Try loading certifi CA bundle
        try:
            import certifi
            ca_bundle = certifi.where()
            if ca_bundle and os.path.isfile(ca_bundle):
                ctx = ssl.create_default_context(cafile=ca_bundle)
        except Exception as ex:
            logger.debug(f"Could not load certifi CA bundle: {ex}")

        if ctx is None:
            ctx = ssl.create_default_context()

        # Load platform/Windows system default root certificates
        try:
            ctx.load_default_certs()
        except Exception as ex:
            logger.debug(f"Could not load system default certificates: {ex}")

        return ctx

    def cancel(self) -> None:
        """Request cancellation of an active download."""
        self._cancel_event.set()

    def download_and_install(
        self,
        progress_callback: Optional[Callable[[int, int, float], None]] = None,
        url: str = OFFICIAL_BUFFALO_L_URL,
    ) -> bool:
        """
        Download buffalo_l.zip from official source, extract, and verify.
        progress_callback signature: (downloaded_bytes, total_bytes, speed_bytes_sec)
        """
        self._cancel_event.clear()
        self._is_downloading = True
        self.target_dir.mkdir(parents=True, exist_ok=True)
        zip_path = self.target_dir / "buffalo_l.zip"
        temp_extract_dir = self.target_dir / "_temp_extract"

        try:
            logger.info(f"Connecting to official model source: {url}")
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "FaceSoter-Desktop/1.0 (Windows)"},
            )

            ssl_context = self._get_ssl_context(verify=True)
            try:
                response = urllib.request.urlopen(req, timeout=30, context=ssl_context)
            except (urllib.error.URLError, ssl.SSLError) as e:
                err_str = str(e)
                reason = getattr(e, "reason", None)
                is_cert_error = (
                    "CERTIFICATE_VERIFY_FAILED" in err_str
                    or "certificate verify failed" in err_str
                    or isinstance(reason, ssl.SSLCertVerificationError)
                )
                if is_cert_error:
                    logger.warning(
                        f"SSL certificate verification failed ({e}). "
                        "Retrying with fallback SSL context..."
                    )
                    ssl_context = self._get_ssl_context(verify=False)
                    response = urllib.request.urlopen(req, timeout=30, context=ssl_context)
                else:
                    raise

            with response:
                total_size = int(response.headers.get("Content-Length", 0))
                downloaded = 0
                start_time = time.time()
                last_time = start_time
                last_downloaded = 0
                speed = 0.0

                with open(zip_path, "wb") as out_file:
                    block_size = 128 * 1024  # 128 KB chunks
                    while True:
                        if self._cancel_event.is_set():
                            logger.info("Model download cancelled by user.")
                            out_file.close()
                            if zip_path.exists():
                                zip_path.unlink()
                            return False

                        buffer = response.read(block_size)
                        if not buffer:
                            break

                        out_file.write(buffer)
                        downloaded += len(buffer)

                        now = time.time()
                        time_delta = now - last_time
                        if time_delta >= 0.5:  # update speed every 0.5s
                            speed = (downloaded - last_downloaded) / time_delta
                            last_time = now
                            last_downloaded = downloaded
                            if progress_callback:
                                progress_callback(downloaded, total_size, speed)

            # Final progress update
            if progress_callback:
                progress_callback(downloaded, total_size, speed)

            logger.info(f"Download finished ({downloaded} bytes). Verifying archive...")

            # Extract archive
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
            temp_extract_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(zip_path, "r") as zf:
                # Test archive integrity
                bad_file = zf.testzip()
                if bad_file:
                    raise ModelVerificationError(f"Corrupted zip archive: {bad_file}")
                zf.extractall(temp_extract_dir)

            # Locate model files inside extracted folder (could be nested inside buffalo_l/)
            extracted_source = temp_extract_dir
            if (temp_extract_dir / "buffalo_l").exists() and (temp_extract_dir / "buffalo_l").is_dir():
                extracted_source = temp_extract_dir / "buffalo_l"

            # Check files
            valid, msg = self.verify_existing(extracted_source)
            if not valid:
                raise ModelVerificationError(f"Extracted files validation failed: {msg}")

            # Move to destination
            if self.model_dir.exists():
                shutil.rmtree(self.model_dir, ignore_errors=True)
            self.model_dir.mkdir(parents=True, exist_ok=True)

            for item in extracted_source.iterdir():
                dest = self.model_dir / item.name
                if item.is_dir():
                    shutil.copytree(item, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(item, dest)

            logger.info(f"Model successfully installed to: {self.model_dir}")
            return True

        except Exception as e:
            logger.error(f"Model download/install failed: {e}")
            raise
        finally:
            self._is_downloading = False
            # Clean up temp files
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except Exception:
                    pass
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir, ignore_errors=True)

    def install_from_local_folder(self, local_folder: Path) -> bool:
        """Install or link model from a user-specified existing local folder."""
        valid, msg = self.verify_existing(local_folder)
        if not valid:
            raise ModelVerificationError(msg)

        self.model_dir.mkdir(parents=True, exist_ok=True)
        for item in local_folder.iterdir():
            if item.suffix.lower() == ".onnx":
                shutil.copy2(item, self.model_dir / item.name)

        logger.info(f"Copied local model files from {local_folder} to {self.model_dir}")
        return True
