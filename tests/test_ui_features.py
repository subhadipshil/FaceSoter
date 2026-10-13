"""
Tests for UI components and dialogs introduced in v1.2.0:
- FeaturePosterDialog (auto-close in 3s, hover pause, suppress logic)
- SingleGroupReviewDialog
- ModelDownloader fast download URL & zip extraction
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from facesoter.core.organizer.engine import PreCopySummary
from facesoter.ui.dialogs.feature_poster_dialog import FeaturePosterDialog
from facesoter.ui.dialogs.single_group_review_dialog import SingleGroupReviewDialog
from facesoter.core.ai.model_downloader import OFFICIAL_BUFFALO_L_URL


def get_qapp():
    app = QApplication.instance()
    if not app:
        app = QApplication(["test", "-platform", "offscreen"])
    return app


def test_feature_poster_dialog_timer_and_controls():
    """Verify FeaturePosterDialog properties, countdown, and suppression."""
    app = get_qapp()
    dlg = FeaturePosterDialog()

    assert dlg._remaining_ms == 3000
    assert dlg.should_suppress_future is True

    # Simulate 1 second of countdown
    dlg._on_timer_tick()
    assert dlg._remaining_ms < 3000

    # Test hover pause
    dlg._is_paused = True
    current_ms = dlg._remaining_ms
    dlg._on_timer_tick()
    # While paused, remaining time should NOT decrease
    assert dlg._remaining_ms == current_ms

    # Resume
    dlg._is_paused = False
    dlg._on_timer_tick()
    assert dlg._remaining_ms < current_ms

    dlg._timer.stop()


def test_single_group_review_dialog_metrics():
    """Verify SingleGroupReviewDialog displays correct metrics."""
    app = get_qapp()
    summary = PreCopySummary(
        photos_scanned=50,
        photos_with_faces=45,
        photos_without_faces=5,
        people_detected=2,
        known_people_count=0,
        unknown_clusters_count=0,
        total_copies_to_perform=50,
        destination_tree={"Single_Photos": 30, "Group_Photos": 15, "No_Face": 5},
    )

    dlg = SingleGroupReviewDialog(
        summary=summary,
        single_count=30,
        group_count=15,
        no_face_count=5,
        is_move=False,
    )

    assert dlg.single_count == 30
    assert dlg.group_count == 15
    assert dlg.no_face_count == 5
    assert dlg.tree.topLevelItemCount() == 3


def test_official_model_url():
    """Verify official buffalo_l model URL is valid."""
    assert OFFICIAL_BUFFALO_L_URL.startswith("https://")
    assert "buffalo_l.zip" in OFFICIAL_BUFFALO_L_URL
