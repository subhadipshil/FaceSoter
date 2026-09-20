"""
Dialog for viewing failed files and error details.
"""

from __future__ import annotations
from typing import List, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTableWidget,
    QTableWidgetItem, QHeaderView, QFileDialog, QMessageBox
)


class FailedFilesDialog(QDialog):
    """Displays table of failed files, errors, and timestamps with export option."""

    def __init__(self, failed_items: List[Dict[str, Any]], parent=None):
        super().__init__(parent)
        self.failed_items = failed_items
        self.setWindowTitle("Failed Files Inspector — FaceSoter")
        self.setMinimumSize(720, 440)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        header = QLabel(f"Failed Files ({len(self.failed_items)} items)")
        header.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(header)

        self.table = QTableWidget(len(self.failed_items), 3)
        self.table.setHorizontalHeaderLabels(["File Path", "Error Reason", "Timestamp"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)

        for row, item in enumerate(self.failed_items):
            self.table.setItem(row, 0, QTableWidgetItem(str(item.get("file_path", ""))))
            self.table.setItem(row, 1, QTableWidgetItem(str(item.get("error_message", "Unknown error"))))
            self.table.setItem(row, 2, QTableWidgetItem(str(item.get("updated_at", ""))))

        layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        export_btn = QPushButton("Export Log...")
        export_btn.clicked.connect(self._export_log)
        btn_layout.addWidget(export_btn)

        btn_layout.addStretch()

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _export_log(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Failed Files Log", "failed_files.txt", "Text Files (*.txt)"
        )
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(f"FaceSoter Failed Files Report ({len(self.failed_items)} entries)\n")
                f.write("=" * 70 + "\n\n")
                for item in self.failed_items:
                    f.write(f"File:  {item.get('file_path')}\n")
                    f.write(f"Error: {item.get('error_message')}\n")
                    f.write(f"Time:  {item.get('updated_at')}\n\n")
            QMessageBox.information(self, "Exported", "Log exported successfully.")
