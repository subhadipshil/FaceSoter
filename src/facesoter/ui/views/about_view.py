"""
About and Third-Party Licenses view for FaceSoter.
"""

from __future__ import annotations
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextEdit, QFrame, QScrollArea, QPushButton
)
from facesoter import __version__
from facesoter.core.licensing.license_manager import LicenseManager
from facesoter.ui.dialogs.donate_dialog import DonateDialog


class AboutView(QWidget):
    """View displaying application credits, model attribution, and third-party notices."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        header = QLabel("About & Licenses")
        header.setProperty("class", "page_header")
        main_layout.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # 1. Product Info & Privacy Guarantee
        info_card = QFrame()
        info_card.setProperty("class", "card_highlight")
        ic_layout = QVBoxLayout(info_card)
        ic_layout.setSpacing(8)

        app_title = QLabel(f"FaceSoter — Version {__version__}")
        app_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        ic_layout.addWidget(app_title)

        privacy_lbl = QLabel(
            "PRIVACY GUARANTEE:\n"
            "Your photos are processed 100% locally on this device. "
            "No photos, thumbnails, or embeddings are transmitted to any cloud or external network service. "
            "Network access is used only once during initial model setup to fetch official InsightFace weights."
        )
        privacy_lbl.setStyleSheet("color: #68d391; font-weight: bold; font-size: 12px; line-height: 1.4;")
        privacy_lbl.setWordWrap(True)
        ic_layout.addWidget(privacy_lbl)
        layout.addWidget(info_card)

        # 2. Support Developer Card (Buy Me a Coffee)
        support_card = QFrame()
        support_card.setProperty("class", "card")
        sc_layout = QHBoxLayout(support_card)
        sc_layout.setContentsMargins(16, 12, 16, 12)

        sc_info = QVBoxLayout()
        sc_title = QLabel("☕ Support FaceSoter Development")
        sc_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #fbbf24;")
        sc_desc = QLabel(
            "FaceSoter is 100% free and open-source. If you enjoy using it, "
            "consider buying a coffee to support continued development!"
        )
        sc_desc.setStyleSheet("color: #a1a1aa; font-size: 12px;")
        sc_desc.setWordWrap(True)
        sc_info.addWidget(sc_title)
        sc_info.addWidget(sc_desc)
        sc_layout.addLayout(sc_info)

        donate_btn = QPushButton("Buy Me a Coffee")
        donate_btn.setStyleSheet(
            "background-color: #17140a; color: #fbbf24; border: 1px solid #78350f; "
            "font-weight: bold; padding: 8px 16px; border-radius: 8px;"
        )
        donate_btn.clicked.connect(self._open_donate)
        sc_layout.addWidget(donate_btn)

        layout.addWidget(support_card)

        # 3. AI Model Attribution Card
        model_card = QFrame()
        model_card.setProperty("class", "card")
        mc_layout = QVBoxLayout(model_card)
        mc_layout.setSpacing(8)

        specs = LicenseManager.get_model_specifications()
        m_title = QLabel("AI Model Architecture: InsightFace Buffalo_L")
        m_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        mc_layout.addWidget(m_title)

        details_str = (
            f"• Detector: {specs['detector']}\n"
            f"• Recognizer: {specs['recognizer']}\n"
            f"• Package Version: {specs['version']} ({specs['approx_size']})\n"
            f"• Official Source: {specs['download_source']}\n"
            f"• Upstream Terms: {specs['license_type']}"
        )
        m_details = QLabel(details_str)
        m_details.setStyleSheet("color: #cccccc; font-size: 12px; line-height: 1.4;")
        mc_layout.addWidget(m_details)
        layout.addWidget(model_card)

        # 3. Model Terms Notice Text
        layout.addWidget(QLabel("Pre-Trained Model License Terms (InsightFace):"))
        model_notice_edit = QTextEdit()
        model_notice_edit.setReadOnly(True)
        model_notice_edit.setText(LicenseManager.get_model_notice())
        model_notice_edit.setFixedHeight(140)
        layout.addWidget(model_notice_edit)

        # 4. Third-Party Software Notices
        layout.addWidget(QLabel("Third-Party Software Attributions:"))
        tp_edit = QTextEdit()
        tp_edit.setReadOnly(True)
        tp_edit.setText(LicenseManager.get_third_party_notices())
        tp_edit.setFixedHeight(180)
        layout.addWidget(tp_edit)

        scroll.setWidget(container)
        main_layout.addWidget(scroll)

    def _open_donate(self) -> None:
        """Open subtle Buy Me a Coffee / Support dialog."""
        dlg = DonateDialog(parent=self)
        dlg.exec()
