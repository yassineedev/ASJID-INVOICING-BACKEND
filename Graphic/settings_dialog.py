import os
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QFileDialog,
    QMessageBox,
)
from PySide6.QtCore import Qt

from settings_store import (
    get_api_url,
    set_api_url,
    get_save_path,
    set_save_path,
)


class SettingsDialog(QDialog):
    """Simple settings page: API endpoint + invoice save folder.

    Kept as a modal dialog rather than a full app "page" since there
    are only two settings today — a dialog is faster to reach, easier
    to reason about for low-literacy users (a single focused task:
    Save or Cancel), and avoids adding page-navigation chrome to the
    main window for something used rarely.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(560)
        self.setModal(True)

        # Reuse the same visual language as the main window so this
        # doesn't look like a bolted-on native dialog.
        self.setStyleSheet("""
            QDialog {
                background-color: #F1F4F8;
            }
            QLabel {
                font-family: 'Segoe UI', Arial, sans-serif;
                color: #1E293B;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 14px;
                font-size: 14px;
                color: #1E293B;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
            }
            QPushButton.action-btn {
                background-color: #FFFFFF;
                color: #334155;
                border: 1.5px solid #CBD5E1;
                border-radius: 8px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton.action-btn:hover {
                background-color: #F8FAFC;
                border-color: #94A3B8;
            }
            QPushButton.primary-btn {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 8px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton.primary-btn:hover {
                background-color: #1D4ED8;
            }
        """)

        self.init_ui()
        self.load_current_values()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 22)
        layout.setSpacing(20)

        title = QLabel("Application Settings")
        title.setStyleSheet("font-size: 18px; font-weight: 700; color: #0F172A;")
        layout.addWidget(title)

        # --- API URL field ---
        api_label = QLabel("Data source (Google Apps Script URL)")
        api_label.setStyleSheet("font-size: 13px; font-weight: 600; color: #64748B;")
        layout.addWidget(api_label)

        self.api_url_input = QLineEdit()
        self.api_url_input.setPlaceholderText("https://script.google.com/macros/s/.../exec")
        self.api_url_input.setMinimumHeight(42)
        layout.addWidget(self.api_url_input)

        # --- Invoice save path field ---
        path_label = QLabel("Invoice save folder")
        path_label.setStyleSheet(
            "font-size: 13px; font-weight: 600; color: #64748B; margin-top: 6px;"
        )
        layout.addWidget(path_label)

        path_row = QHBoxLayout()
        path_row.setSpacing(10)

        self.save_path_input = QLineEdit()
        self.save_path_input.setPlaceholderText("Folder where generated invoices are saved")
        self.save_path_input.setMinimumHeight(42)

        browse_btn = QPushButton("Browse...")
        browse_btn.setProperty("class", "action-btn")
        browse_btn.setMinimumHeight(42)
        browse_btn.clicked.connect(self.browse_for_folder)

        path_row.addWidget(self.save_path_input)
        path_row.addWidget(browse_btn)
        layout.addLayout(path_row)

        layout.addStretch()

        # --- Save / Cancel ---
        button_row = QHBoxLayout()
        button_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setProperty("class", "action-btn")
        cancel_btn.setMinimumHeight(44)
        cancel_btn.clicked.connect(self.reject)

        save_btn = QPushButton("Save")
        save_btn.setProperty("class", "primary-btn")
        save_btn.setMinimumHeight(44)
        save_btn.clicked.connect(self.save_and_close)

        button_row.addWidget(cancel_btn)
        button_row.addWidget(save_btn)
        layout.addLayout(button_row)

    def load_current_values(self):
        self.api_url_input.setText(get_api_url())
        self.save_path_input.setText(get_save_path())

    def browse_for_folder(self):
        start_dir = self.save_path_input.text().strip() or os.path.expanduser("~")
        chosen = QFileDialog.getExistingDirectory(
            self, "Choose Invoice Save Folder", start_dir
        )
        if chosen:
            self.save_path_input.setText(chosen)

    def save_and_close(self):
        api_url = self.api_url_input.text().strip()
        save_path = self.save_path_input.text().strip()

        if not api_url:
            QMessageBox.warning(self, "Missing API URL", "Please enter a data source URL.")
            return

        if not save_path:
            QMessageBox.warning(
                self, "Missing Save Folder", "Please choose a folder to save invoices to."
            )
            return

        if not os.path.isdir(save_path):
            answer = QMessageBox.question(
                self,
                "Folder Doesn't Exist",
                f"The folder:\n{save_path}\ndoesn't exist yet. Create it now?",
            )
            if answer == QMessageBox.StandardButton.Yes:
                try:
                    os.makedirs(save_path, exist_ok=True)
                except OSError as e:
                    QMessageBox.critical(
                        self, "Could Not Create Folder", f"Error: {e}"
                    )
                    return
            else:
                return

        set_api_url(api_url)
        set_save_path(save_path)
        self.accept()