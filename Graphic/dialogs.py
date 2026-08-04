# dialogs.py
import sys
import os
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
)
from PySide6.QtCore import Qt, QCoreApplication
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QProgressBar,
    QGraphicsDropShadowEffect,
)


class ModernDialog(QDialog):
    def __init__(self, parent=None, width=480, height=260):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(width, height)

        self.card = QFrame(self)
        self.card.setObjectName("dialogCard")
        self.card.setStyleSheet("""
            #dialogCard {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        self.card.setGeometry(12, 12, width - 24, height - 24)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        self.layout = QVBoxLayout(self.card)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(18)

    def add_icon(self, emoji, bg_color, text_color):
        icon = QLabel(emoji)
        icon.setFixedSize(68, 68)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("""
            QLabel {
                background-color: %s;
                color: %s;
                border-radius: 34px;
                font-size: 28px;
                font-weight: 700;
            }
        """ % (bg_color, text_color))
        self.layout.addWidget(icon, alignment=Qt.AlignmentFlag.AlignCenter)
        return icon

    def add_title(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self.layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        return lbl

    def add_message(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-size: 14px; color: #475569; line-height: 1.5;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        self.layout.addWidget(lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        return lbl

    def add_button_row(self, *buttons):
        row = QHBoxLayout()
        row.addStretch()
        for btn in buttons:
            row.addWidget(btn)
        self.layout.addLayout(row)


class CustomMessageBox:
    @staticmethod
    def info(parent, title, text):
        dlg = ModernDialog(parent, 460, 300)
        dlg.add_icon("i", "#DBEAFE", "#2563EB")
        dlg.add_title(title)
        dlg.add_message(text)
        btn = QPushButton("OK")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #2563EB; color: #FFFFFF; border: none;
                border-radius: 10px; padding: 12px 32px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #1D4ED8; }
            QPushButton:pressed { background-color: #1E40AF; }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.clicked.connect(dlg.accept)
        dlg.add_button_row(btn)
        dlg.exec()

    @staticmethod
    def warning(parent, title, text):
        dlg = ModernDialog(parent, 460, 300)
        dlg.add_icon("!", "#FEF3C7", "#D97706")
        dlg.add_title(title)
        dlg.add_message(text)
        btn = QPushButton("Continuer")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #F59E0B; color: #FFFFFF; border: none;
                border-radius: 10px; padding: 12px 32px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #D97706; }
            QPushButton:pressed { background-color: #B45309; }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.clicked.connect(dlg.accept)
        dlg.add_button_row(btn)
        dlg.exec()

    @staticmethod
    def critical(parent, title, text):
        dlg = ModernDialog(parent, 460, 320)
        dlg.add_icon("X", "#FEE2E2", "#DC2626")
        dlg.add_title(title)
        dlg.add_message(text)
        btn = QPushButton("Fermer")
        btn.setStyleSheet("""
            QPushButton {
                background-color: #EF4444; color: #FFFFFF; border: none;
                border-radius: 10px; padding: 12px 32px;
                font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #DC2626; }
            QPushButton:pressed { background-color: #B91C1C; }
        """)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setMinimumHeight(44)
        btn.clicked.connect(dlg.accept)
        dlg.add_button_row(btn)
        dlg.exec()


class InvoiceProgressDialog(QDialog):
    def __init__(self, total_items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(480, 280)
        self.is_canceled = False

        self.card = QFrame(self)
        self.card.setObjectName("progCard")
        self.card.setStyleSheet("""
            #progCard {
                background-color: #FFFFFF;
                border-radius: 20px;
                border: 1px solid #E2E8F0;
            }
        """)
        self.card.setGeometry(12, 12, 480 - 24, 280 - 24)

        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self.card)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(20)

        self.title_label = QLabel("Generation des factures")
        self.title_label.setStyleSheet(
            "font-size: 20px; font-weight: 700; color: #0F172A;"
        )

        self.status_label = QLabel("Preparation...")
        self.status_label.setStyleSheet("font-size: 14px; color: #64748B;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(total_items)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(12)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #E2E8F0;
                border: none;
                border-radius: 6px;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 6px;
            }
        """)

        info_row = QHBoxLayout()
        self.counter_label = QLabel("0 / %d" % total_items)
        self.counter_label.setStyleSheet(
            "font-size: 13px; color: #64748B; font-weight: 600;"
        )
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet(
            "font-size: 13px; color: #2563EB; font-weight: 700;"
        )
        info_row.addWidget(self.counter_label)
        info_row.addStretch()
        info_row.addWidget(self.percent_label)

        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_cancel.setMinimumHeight(42)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC; color: #334155;
                border: 1.5px solid #E2E8F0; border-radius: 10px;
                padding: 10px 28px; font-size: 14px; font-weight: 600;
            }
            QPushButton:hover { background-color: #F1F5F9; border-color: #CBD5E1; }
            QPushButton:pressed { background-color: #E2E8F0; }
        """)
        self.btn_cancel.clicked.connect(self.cancel_clicked)

        layout.addWidget(self.title_label)
        layout.addWidget(self.status_label)
        layout.addWidget(self.progress_bar)
        layout.addLayout(info_row)
        layout.addStretch()
        layout.addWidget(self.btn_cancel, alignment=Qt.AlignmentFlag.AlignRight)

    def cancel_clicked(self):
        self.is_canceled = True
        self.btn_cancel.setEnabled(False)
        self.status_label.setText("Annulation en cours...")

    def update_progress(self, current_val, user_name):
        self.progress_bar.setValue(current_val)
        self.status_label.setText("Generation pour : %s" % user_name)
        total = self.progress_bar.maximum()
        self.counter_label.setText("%d / %d" % (current_val, total))
        if total > 0:
            self.percent_label.setText("%d%%" % int((current_val / total) * 100))
        QCoreApplication.processEvents()

    def wasCanceled(self):
        return self.is_canceled
