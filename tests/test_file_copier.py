"""
Unit tests for SafeFileCopier, atomic write, and collision resolution.
"""

import tempfile
import os
from pathlib import Path
import pytest
from facesoter.core.organizer.file_copier import SafeFileCopier


@pytest.fixture
def temp_dirs():
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dst:
        yield Path(src), Path(dst)


def test_atomic_file_copy(temp_dirs):
    src_dir, dst_dir = temp_dirs
    copier = SafeFileCopier()

    test_file = src_dir / "sample.jpg"
    test_content = b"fake_jpeg_content_header_12345"
    test_file.write_bytes(test_content)

    success, final_path, err = copier.copy_file_atomic(test_file, dst_dir)
    assert success is True
    assert err is None
    assert Path(final_path).exists()
    assert Path(final_path).read_bytes() == test_content
    # Original must remain intact
    assert test_file.exists()


def test_filename_collision_different_content(temp_dirs):
    """When a file with the same name but different content exists, rename with number."""
    src_dir, dst_dir = temp_dirs
    copier = SafeFileCopier(collision_policy="rename_numbered", detect_duplicates=True)

    # Destination already has an existing sample.jpg
    existing_dest = dst_dir / "sample.jpg"
    existing_dest.write_bytes(b"existing_file_content")

    # Source has different content
    src_file = src_dir / "sample.jpg"
    src_file.write_bytes(b"new_different_content")

    success, final_path, err = copier.copy_file_atomic(src_file, dst_dir)
    assert success is True
    assert Path(final_path).name == "sample_1.jpg"
    assert Path(final_path).read_bytes() == b"new_different_content"
    assert existing_dest.read_bytes() == b"existing_file_content"


def test_duplicate_content_skipped(temp_dirs):
    """When a file with identical content exists at destination, skip copy."""
    src_dir, dst_dir = temp_dirs
    copier = SafeFileCopier(collision_policy="rename_numbered", detect_duplicates=True)

    content = b"identical_photo_content_bytes"
    (dst_dir / "sample.jpg").write_bytes(content)

    src_file = src_dir / "sample.jpg"
    src_file.write_bytes(content)

    success, final_path, err = copier.copy_file_atomic(src_file, dst_dir)
    assert success is True
    assert "Skipped" in err
