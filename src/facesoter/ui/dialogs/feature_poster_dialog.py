"""
Announcement poster dialog for the new Single & Group Photo Separator feature.
Auto-closes in 3 seconds in a smooth, non-annoying manner, with options to try the feature or dismiss.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QProgressBar, QCheckBox, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QColor


class FeaturePosterDialog(QDialog):
    """
    Sleek, non-intrusive feature announcement poster.
    Auto-closes after 3 seconds unless hovered, and provides a 1-click action to try the feature.
    """

    try_feature_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Feature — Single & Group Photo Separator")
        self.setFixedWidth(560)
        self.setModal(True)

        self._remaining_ms = 3000
        self._step_interval = 50  # updates every 50ms for buttery-smooth progress
        self._is_paused = False

        self._init_ui()
        self._setup_timer()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 20)
        layout.setSpacing(16)

        # Outer Container Card
        container = QFrame()
        container.setObjectName("poster_container")
        container.setStyleSheet("""
            QFrame#poster_container {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #18181b, stop:1 #111113);
                border: 1px solid #27272a;
                border-radius: 12px;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setContentsMargins(20, 20, 20, 20)
        c_layout.setSpacing(14)

        # Top Badge & Close 'X' Button
        top_row = QHBoxLayout()
        badge = QLabel("✨ NEW FEATURE")
        badge.setStyleSheet("""
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #8b5cf6);
            color: #ffffff;
            font-size: 11px;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 10px;
            letter-spacing: 0.5px;
        """)
        top_row.addWidget(badge)
        top_row.addStretch()

        close_x = QPushButton("✕")
        close_x.setFixedSize(28, 28)
        close_x.setCursor(Qt.CursorShape.PointingHandCursor)
        close_x.setStyleSheet("""
            QPushButton {
                background: #27272a;
                color: #a1a1aa;
                border-radius: 14px;
                font-size: 13px;
                font-weight: bold;
                border: 1px solid #3f3f46;
            }
            QPushButton:hover {
                background: #3f3f46;
                color: #ffffff;
            }
        """)
        close_x.clicked.connect(self.reject)
        top_row.addWidget(close_x)
        c_layout.addLayout(top_row)

        # Poster Title & Tagline
        title = QLabel("Single & Group Photo Separator")
        title.setStyleSheet("font-size: 21px; font-weight: 800; color: #ffffff; margin-top: 2px;")
        c_layout.addWidget(title)

        tagline = QLabel(
            "Quickly separate solo portraits from family and group photos with intelligent on-device face count detection."
        )
        tagline.setWordWrap(True)
        tagline.setStyleSheet("font-size: 13px; color: #a1a1aa; line-height: 1.4;")
        c_layout.addWidget(tagline)

        # Feature Highlights Visual Card
        highlight_box = QFrame()
        highlight_box.setStyleSheet("""
            background-color: #1f1f23;
            border: 1px solid #2d2d32;
            border-radius: 8px;
            padding: 4px;
        """)
        hb_layout = QVBoxLayout(highlight_box)
        hb_layout.setSpacing(10)
        hb_layout.setContentsMargins(14, 12, 14, 12)

        def add_feature_bullet(icon: str, heading: str, sub: str):
            row = QHBoxLayout()
            row.setSpacing(12)
            icon_lbl = QLabel(icon)
            icon_lbl.setStyleSheet("font-size: 20px; background: transparent;")
            icon_lbl.setFixedWidth(28)
            row.addWidget(icon_lbl)

            text_layout = QVBoxLayout()
            text_layout.setSpacing(2)
            h = QLabel(heading)
            h.setStyleSheet("font-size: 12px; font-weight: 700; color: #f4f4f5; background: transparent;")
            s = QLabel(sub)
            s.setStyleSheet("font-size: 11px; color: #94a3b8; background: transparent;")
            text_layout.addWidget(h)
            text_layout.addWidget(s)
            row.addLayout(text_layout)
            hb_layout.addLayout(row)

        add_feature_bullet("👤", "Single Photo Detection", "Photos with 1 detected face are copied into Single_Photos/")
        add_feature_bullet("👥", "Group Photo Detection", "Photos with 2+ detected faces are copied into Group_Photos/")
        add_feature_bullet("⚡", "Fast, Private & Non-Destructive", "100% offline SCRFD detector with safe atomic copying & EXIF preservation")

        c_layout.addWidget(highlight_box)

        # Progress / Auto-Close Bar
        timer_box = QVBoxLayout()
        timer_box.setSpacing(4)
        self.countdown_label = QLabel("Auto-closing in 3.0s...")
        self.countdown_label.setStyleSheet("color: #71717a; font-size: 11px;")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        timer_box.addWidget(self.countdown_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 3000)
        self.progress_bar.setValue(3000)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFixedHeight(4)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #27272a;
                border-radius: 2px;
                border: none;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0284c7, stop:1 #38bdf8);
                border-radius: 2px;
            }
        """)
        timer_box.addWidget(self.progress_bar)
        c_layout.addLayout(timer_box)

        # Bottom Controls: Don't show again + Action Buttons
        bot_layout = QHBoxLayout()
        bot_layout.setContentsMargins(0, 6, 0, 0)

        self.dont_show_check = QCheckBox("Don't show again")
        self.dont_show_check.setChecked(True)
        self.dont_show_check.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        bot_layout.addWidget(self.dont_show_check)

        bot_layout.addStretch()

        self.dismiss_btn = QPushButton("Dismiss")
        self.dismiss_btn.setStyleSheet("""
            QPushButton {
                background-color: #27272a;
                color: #e4e4e7;
                border: 1px solid #3f3f46;
                padding: 7px 16px;
                border-radius: 6px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #3f3f46;
                color: #ffffff;
            }
        """)
        self.dismiss_btn.clicked.connect(self.reject)
        bot_layout.addWidget(self.dismiss_btn)

        self.try_btn = QPushButton("Try Feature Now 🚀")
        self.try_btn.setProperty("class", "btn_primary")
        self.try_btn.setStyleSheet("""
            QPushButton {
                background-color: #0284c7;
                color: #ffffff;
                border: 1px solid #38bdf8;
                padding: 7px 18px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0369a1;
            }
        """)
        self.try_btn.clicked.connect(self._on_try_feature)
        bot_layout.addWidget(self.try_btn)

        c_layout.addLayout(bot_layout)
        layout.addWidget(container)

    def _setup_timer(self) -> None:
        self._timer = QTimer(self)
        self._timer.setInterval(self._step_interval)
        self._timer.timeout.connect(self._on_timer_tick)
        self._timer.start()

    def _on_timer_tick(self) -> None:
        if self._is_paused:
            return

        self._remaining_ms -= self._step_interval
        if self._remaining_ms <= 0:
            self._timer.stop()
            self.accept()
            return

        self.progress_bar.setValue(max(0, self._remaining_ms))
        sec = self._remaining_ms / 1000.0
        self.countdown_label.setText(f"Auto-closing in {sec:.1f}s...")

    def enterEvent(self, event) -> None:
        """Pause timer when user hovers to read comfortably."""
        self._is_paused = True
        self.countdown_label.setText("Paused while hovering...")
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:
        """Resume countdown when user moves cursor away."""
        self._is_paused = False
        super().leaveEvent(event)

    def _on_try_feature(self) -> None:
        self._timer.stop()
        self.try_feature_requested.emit()
        self.accept()

    @property
    def should_suppress_future(self) -> bool:
        """Returns True if the user requested not to see the popup again."""
        return self.dont_show_check.isChecked()
