"""
Subtle, elegant 'Buy Me a Coffee' dialog with UPI QR code and one-click copy.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QApplication
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QIcon
from facesoter.ui.assets import get_asset_path


UPI_ID = "subhadipshil.pnb@ybl"


class DonateDialog(QDialog):
    """Subtle, non-intrusive donation dialog for user support."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Support FaceSoter — Buy Me a Coffee")
        self.setFixedSize(440, 560)
        self.setModal(True)

        icon_path = get_asset_path("icons/app_icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        # Header Title
        title = QLabel("☕ Buy Me a Coffee")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f59e0b;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Subtitle
        sub = QLabel(
            "FaceSoter is 100% free, private, and local-first with zero tracking. "
            "If it saved you hours organizing your memories, buying a coffee is a great "
            "way to support continued development!"
        )
        sub.setWordWrap(True)
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #a1a1aa; font-size: 12px; line-height: 1.4;")
        layout.addWidget(sub)

        # QR Code Card Container
        qr_card = QFrame()
        qr_card.setStyleSheet(
            "background-color: #ffffff; border-radius: 12px; padding: 10px; border: 1px solid #3f3f46;"
        )
        qr_layout = QVBoxLayout(qr_card)
        qr_layout.setContentsMargins(8, 8, 8, 8)
        qr_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        qr_label = QLabel()
        qr_path = get_asset_path("donate_qr.png")
        if qr_path.exists():
            pix = QPixmap(str(qr_path)).scaled(
                220, 220, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            qr_label.setPixmap(pix)
        else:
            qr_label.setText("Scan UPI QR")
            qr_label.setStyleSheet("color: #000000; font-weight: bold;")
        qr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        qr_layout.addWidget(qr_label)
        layout.addWidget(qr_card, alignment=Qt.AlignmentFlag.AlignCenter)

        # Instruction
        scan_hint = QLabel("Scan using Google Pay, PhonePe, Paytm, or any UPI App")
        scan_hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scan_hint.setStyleSheet("color: #71717a; font-size: 11px; font-weight: 500;")
        layout.addWidget(scan_hint)

        # UPI ID Copy Box
        upi_box = QFrame()
        upi_box.setStyleSheet(
            "background-color: #18181b; border: 1px solid #27272a; border-radius: 8px; padding: 4px;"
        )
        upi_layout = QHBoxLayout(upi_box)
        upi_layout.setContentsMargins(10, 6, 6, 6)

        upi_label = QLabel(UPI_ID)
        upi_label.setStyleSheet("font-family: monospace; font-size: 13px; color: #38bdf8; font-weight: bold;")
        upi_layout.addWidget(upi_label)

        self.copy_btn = QPushButton("Copy UPI ID")
        self.copy_btn.setStyleSheet(
            "background-color: #27272a; color: #ffffff; border: 1px solid #3f3f46; "
            "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
        )
        self.copy_btn.clicked.connect(self._copy_upi)
        upi_layout.addWidget(self.copy_btn)

        layout.addWidget(upi_box)

        # Close button
        layout.addStretch()
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        close_btn.setStyleSheet("padding: 8px 24px; border-radius: 6px;")
        layout.addWidget(close_btn, alignment=Qt.AlignmentFlag.AlignCenter)

    def _copy_upi(self) -> None:
        QApplication.clipboard().setText(UPI_ID)
        self.copy_btn.setText("✓ Copied!")
        self.copy_btn.setStyleSheet(
            "background-color: #065f46; color: #34d399; border: 1px solid #059669; "
            "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
        )
        QTimer.singleShot(2500, self._reset_copy_btn)

    def _reset_copy_btn(self) -> None:
        self.copy_btn.setText("Copy UPI ID")
        self.copy_btn.setStyleSheet(
            "background-color: #27272a; color: #ffffff; border: 1px solid #3f3f46; "
            "border-radius: 6px; padding: 5px 12px; font-size: 11px; font-weight: 600;"
        )
