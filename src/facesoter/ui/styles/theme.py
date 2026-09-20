"""
Theme definitions and Qt stylesheet for FaceSoter.
"""

DARK_THEME_QSS = """
/* FaceSoter Modern Windows Desktop Dark Theme */

QWidget {
    background-color: #1e1e1e;
    color: #f1f1f1;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 13px;
    border: none;
}

/* Main Window & Sidebar */
QMainWindow {
    background-color: #181818;
}

QFrame#sidebar {
    background-color: #141414;
    border-right: 1px solid #2d2d30;
    min-width: 220px;
    max-width: 220px;
}

QLabel#app_title {
    font-size: 18px;
    font-weight: bold;
    color: #ffffff;
    padding: 16px 12px 6px 12px;
}

QLabel#app_subtitle {
    font-size: 11px;
    color: #888888;
    padding: 0 12px 16px 12px;
}

/* Sidebar navigation buttons */
QPushButton.nav_btn {
    text-align: left;
    padding: 10px 16px;
    margin: 2px 8px;
    border-radius: 6px;
    color: #cccccc;
    background-color: transparent;
    font-size: 13px;
    font-weight: 500;
}

QPushButton.nav_btn:hover {
    background-color: #252528;
    color: #ffffff;
}

QPushButton.nav_btn:checked, QPushButton.nav_btn[active="true"] {
    background-color: #0078d4;
    color: #ffffff;
    font-weight: bold;
}

/* Content Area */
QStackedWidget#content_area {
    background-color: #1e1e1e;
    padding: 16px;
}

/* Card Containers */
QFrame.card {
    background-color: #252526;
    border: 1px solid #333337;
    border-radius: 8px;
    padding: 16px;
}

QFrame.card_highlight {
    background-color: #28282c;
    border: 1px solid #0078d4;
    border-radius: 8px;
    padding: 16px;
}

/* Typography */
QLabel.page_header {
    font-size: 22px;
    font-weight: bold;
    color: #ffffff;
    margin-bottom: 4px;
}

QLabel.page_subheader {
    font-size: 13px;
    color: #999999;
    margin-bottom: 16px;
}

QLabel.section_title {
    font-size: 15px;
    font-weight: bold;
    color: #e0e0e0;
    margin-top: 8px;
    margin-bottom: 8px;
}

QLabel.metric_value {
    font-size: 26px;
    font-weight: bold;
    color: #ffffff;
}

QLabel.metric_label {
    font-size: 11px;
    color: #888888;
    text-transform: uppercase;
    font-weight: 600;
}

/* Buttons */
QPushButton {
    background-color: #333337;
    color: #ffffff;
    border: 1px solid #454549;
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}

QPushButton:hover {
    background-color: #3e3e42;
    border-color: #555559;
}

QPushButton:pressed {
    background-color: #252526;
}

QPushButton:disabled {
    background-color: #252526;
    color: #666666;
    border-color: #2e2e30;
}

QPushButton.btn_primary {
    background-color: #0078d4;
    border: 1px solid #1084d8;
    color: #ffffff;
    font-weight: bold;
}

QPushButton.btn_primary:hover {
    background-color: #1988e0;
    border-color: #2894ea;
}

QPushButton.btn_primary:pressed {
    background-color: #0060aa;
}

QPushButton.btn_success {
    background-color: #107c41;
    border: 1px solid #148b4b;
    color: #ffffff;
    font-weight: bold;
}

QPushButton.btn_success:hover {
    background-color: #16934e;
}

QPushButton.btn_danger {
    background-color: #a80000;
    border: 1px solid #b81010;
    color: #ffffff;
}

QPushButton.btn_danger:hover {
    background-color: #c41212;
}

/* Line Edits & Inputs */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #2d2d30;
    color: #ffffff;
    border: 1px solid #3e3e42;
    border-radius: 5px;
    padding: 6px 10px;
    selection-background-color: #0078d4;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #0078d4;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

/* Tables */
QTableWidget, QTableView {
    background-color: #252526;
    border: 1px solid #333337;
    border-radius: 6px;
    gridline-color: #2d2d30;
    selection-background-color: #0078d4;
    selection-color: #ffffff;
}

QHeaderView::section {
    background-color: #1e1e1e;
    color: #cccccc;
    font-weight: 600;
    padding: 8px 10px;
    border: none;
    border-bottom: 1px solid #333337;
    border-right: 1px solid #2d2d30;
}

/* Progress Bars */
QProgressBar {
    background-color: #2d2d30;
    border: 1px solid #3e3e42;
    border-radius: 4px;
    text-align: center;
    color: #ffffff;
    font-weight: bold;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #0078d4;
    border-radius: 3px;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #2d2d30;
}

QCheckBox::indicator:hover {
    border-color: #0078d4;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

/* Scrollbars */
QScrollBar:vertical {
    background: #1e1e1e;
    width: 10px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #424245;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #555559;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #141414;
    border-top: 1px solid #2d2d30;
    color: #999999;
    font-size: 12px;
}
"""
