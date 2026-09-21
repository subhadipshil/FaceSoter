"""
Modern, polished Dark Theme stylesheet for FaceSoter.
Designed with Fluent / Obsidian Dark principles, crisp typography, and harmonious micro-accents.
"""

DARK_THEME_QSS = """
/* ==============================================================================
   Base Application & Global Elements
   ============================================================================== */
QWidget {
    background-color: #121214;
    color: #f4f4f5;
    font-family: "Segoe UI", -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    border: none;
}

QMainWindow {
    background-color: #121214;
}

/* ==============================================================================
   Sidebar Navigation & Branding
   ============================================================================== */
QFrame#sidebar {
    background-color: #0d0d0f;
    border-right: 1px solid #202024;
    min-width: 228px;
    max-width: 228px;
}

QLabel#app_title {
    font-size: 17px;
    font-weight: 800;
    color: #ffffff;
    letter-spacing: 0.5px;
}

QLabel#version_badge {
    background-color: #1e293b;
    color: #38bdf8;
    font-size: 10px;
    font-weight: 700;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #0284c7;
}

QLabel#app_subtitle {
    font-size: 11px;
    color: #71717a;
    font-weight: 500;
}

/* Sidebar navigation buttons */
QPushButton.nav_btn {
    text-align: left;
    padding: 9px 14px;
    margin: 2px 8px;
    border-radius: 8px;
    color: #a1a1aa;
    background-color: transparent;
    font-size: 13px;
    font-weight: 500;
    border: 1px solid transparent;
}

QPushButton.nav_btn:hover {
    background-color: #1c1c20;
    color: #ffffff;
    border: 1px solid #27272a;
}

QPushButton.nav_btn:checked, QPushButton.nav_btn[active="true"] {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 700;
    border: 1px solid #38bdf8;
}

/* Subtle Buy Me a Coffee button */
QPushButton#btn_coffee {
    text-align: left;
    padding: 8px 14px;
    margin: 2px 8px;
    border-radius: 8px;
    color: #fbbf24;
    background-color: #17140a;
    border: 1px solid #451a03;
    font-size: 12px;
    font-weight: 600;
}

QPushButton#btn_coffee:hover {
    background-color: #291e0a;
    color: #fde68a;
    border: 1px solid #d97706;
}

QPushButton#btn_coffee:pressed {
    background-color: #0f0d06;
}

/* ==============================================================================
   Content Area & Cards
   ============================================================================== */
QStackedWidget#content_area {
    background-color: #121214;
    padding: 18px;
}

QFrame.card {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 10px;
    padding: 16px;
}

QFrame.card_highlight {
    background-color: #181c24;
    border: 1px solid #0284c7;
    border-radius: 10px;
    padding: 16px;
}

QFrame.card:hover {
    border-color: #3f3f46;
}

QFrame.card_highlight:hover {
    border-color: #38bdf8;
}

/* ==============================================================================
   Typography & Badges
   ============================================================================== */
QLabel.page_header {
    font-size: 22px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 2px;
    letter-spacing: -0.3px;
}

QLabel.page_subheader {
    font-size: 13px;
    color: #71717a;
    margin-bottom: 16px;
}

QLabel.section_title {
    font-size: 14px;
    font-weight: 700;
    color: #e4e4e7;
    margin-top: 6px;
    margin-bottom: 6px;
}

QLabel.metric_value {
    font-size: 28px;
    font-weight: 800;
    color: #ffffff;
}

QLabel.metric_label {
    font-size: 11px;
    color: #71717a;
    text-transform: uppercase;
    font-weight: 700;
    letter-spacing: 0.5px;
}

/* ==============================================================================
   Buttons
   ============================================================================== */
QPushButton {
    background-color: #202024;
    color: #f4f4f5;
    border: 1px solid #2e2e33;
    border-radius: 8px;
    padding: 8px 18px;
    font-weight: 600;
    font-size: 13px;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #27272a;
    border-color: #3f3f46;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #18181b;
}

QPushButton:disabled {
    background-color: #18181b;
    color: #52525b;
    border-color: #202024;
}

/* Primary Action Button */
QPushButton.btn_primary {
    background-color: #0284c7;
    border: 1px solid #38bdf8;
    color: #ffffff;
    font-weight: 700;
}

QPushButton.btn_primary:hover {
    background-color: #0369a1;
    border-color: #7dd3fc;
}

QPushButton.btn_primary:pressed {
    background-color: #075985;
}

/* Success Button */
QPushButton.btn_success {
    background-color: #059669;
    border: 1px solid #34d399;
    color: #ffffff;
    font-weight: 700;
}

QPushButton.btn_success:hover {
    background-color: #047857;
    border-color: #6ee7b7;
}

/* Danger Button */
QPushButton.btn_danger {
    background-color: #991b1b;
    border: 1px solid #ef4444;
    color: #ffffff;
    font-weight: 600;
}

QPushButton.btn_danger:hover {
    background-color: #b91c1c;
    border-color: #f87171;
}

/* ==============================================================================
   Input Fields & Selectors
   ============================================================================== */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #18181b;
    color: #ffffff;
    border: 1px solid #27272a;
    border-radius: 7px;
    padding: 7px 12px;
    selection-background-color: #0284c7;
    font-size: 13px;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #0284c7;
    background-color: #1c1c20;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #18181b;
    border: 1px solid #27272a;
    selection-background-color: #0284c7;
    color: #ffffff;
    padding: 4px;
}

/* ==============================================================================
   Tables & Data Grids
   ============================================================================== */
QTableWidget, QTableView {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    gridline-color: #202024;
    selection-background-color: #0284c7;
    selection-color: #ffffff;
    alternate-background-color: #151518;
}

QHeaderView::section {
    background-color: #121214;
    color: #a1a1aa;
    font-weight: 700;
    font-size: 12px;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #27272a;
    border-right: 1px solid #1a1a1e;
}

/* Lists */
QListWidget {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 6px;
}

QListWidget::item {
    padding: 8px 12px;
    border-radius: 6px;
    color: #e4e4e7;
}

QListWidget::item:hover {
    background-color: #202024;
}

QListWidget::item:selected {
    background-color: #0284c7;
    color: #ffffff;
    font-weight: 700;
}

/* ==============================================================================
   Progress Bars
   ============================================================================== */
QProgressBar {
    background-color: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    text-align: center;
    color: #ffffff;
    font-weight: 700;
    font-size: 11px;
    height: 16px;
}

QProgressBar::chunk {
    background-color: #0284c7;
    border-radius: 5px;
}

/* ==============================================================================
   Checkboxes & Radio Buttons
   ============================================================================== */
QCheckBox {
    spacing: 8px;
    color: #e4e4e7;
    font-size: 13px;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3f3f46;
    border-radius: 5px;
    background-color: #18181b;
}

QCheckBox::indicator:hover {
    border-color: #0284c7;
}

QCheckBox::indicator:checked {
    background-color: #0284c7;
    border-color: #38bdf8;
}

/* ==============================================================================
   Scrollbars
   ============================================================================== */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #27272a;
    border-radius: 4px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #3f3f46;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* ==============================================================================
   Status Bar
   ============================================================================== */
QStatusBar {
    background-color: #0d0d0f;
    border-top: 1px solid #202024;
    color: #71717a;
    font-size: 12px;
    padding: 2px 10px;
}
"""
