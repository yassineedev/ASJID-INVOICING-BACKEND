import sys
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QHBoxLayout,
    QTableWidget,
    QTableWidgetItem,
    QLineEdit,
    QFrame,
    QHeaderView,
    QProgressBar,
    QDialog,
    QGraphicsDropShadowEffect,
)
from PySide6.QtCore import Qt, QSize, QCoreApplication
from PySide6.QtGui import QFont, QColor, QIcon
# Import backend worker and generator
from workers import FetchUsersWorker
from invoice import Generator, GeneratorError
from settings_dialog import SettingsDialog
from settings_store import get_save_path


# =============================================================================
#  EASY MODERN DIALOG BASE
# =============================================================================

class ModernDialog(QDialog):
    """Simple frameless dialog with a rounded white card and soft shadow."""

    def __init__(self, parent=None, width=480, height=260):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Dialog)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setModal(True)
        self.setFixedSize(width, height)

        # Rounded card
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

        # Soft shadow
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(50)
        shadow.setColor(QColor(0, 0, 0, 40))
        shadow.setOffset(0, 10)
        self.card.setGraphicsEffect(shadow)

        # Content layout inside card
        self.layout = QVBoxLayout(self.card)
        self.layout.setContentsMargins(32, 32, 32, 32)
        self.layout.setSpacing(18)

    def add_icon(self, emoji, bg_color, text_color):
        """Add a circular icon label."""
        icon = QLabel(emoji)
        icon.setFixedSize(68, 68)
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 34px;
                font-size: 28px;
                font-weight: 700;
            }}
        """)
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
    """Same static API, but uses the new modern look."""

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
        dlg.add_icon("✕", "#FEE2E2", "#DC2626")
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

        self.title_label = QLabel("Génération des factures")
        self.title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")

        self.status_label = QLabel("Préparation...")
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
        self.counter_label = QLabel(f"0 / {total_items}")
        self.counter_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 600;")
        self.percent_label = QLabel("0%")
        self.percent_label.setStyleSheet("font-size: 13px; color: #2563EB; font-weight: 700;")
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
        self.status_label.setText(f"Génération pour : {user_name}")
        total = self.progress_bar.maximum()
        self.counter_label.setText(f"{current_val} / {total}")
        if total > 0:
            self.percent_label.setText(f"{int((current_val / total) * 100)}%")
        QCoreApplication.processEvents()

    def wasCanceled(self):
        return self.is_canceled


# =============================================================================
#  MAIN APPLICATION
# =============================================================================

class WaterAssociationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASJID")
        self.setWindowIcon(QIcon("app_icon.ico"))
        self.resize(1440, 900)
        self.setMinimumSize(QSize(1280, 800))

        self.raw_data = []
        self.api_records = []
        self.current_view = "all"

        self.setup_styles()
        self.init_ui()
        self.load_data_from_api()

    # ------------------------------------------------------------------
    # STYLES
    # ------------------------------------------------------------------
    def setup_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }
            QMainWindow QLabel {
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
                color: #0F172A;
            }
            QPushButton.action-btn {
                background-color: #FFFFFF;
                color: #334155;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px 22px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton.action-btn:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
            QPushButton.action-btn:pressed {
                background-color: #F1F5F9;
            }
            QPushButton.action-btn-active {
                background-color: #EFF6FF;
                color: #1D4ED8;
                border: 1.5px solid #2563EB;
                border-radius: 10px;
                padding: 12px 22px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton.primary-btn {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-size: 14px;
                font-weight: 700;
            }
            QPushButton.primary-btn:hover {
                background-color: #1D4ED8;
            }
            QPushButton.primary-btn:pressed {
                background-color: #1E40AF;
            }
            QLineEdit {
                background-color: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 12px 16px;
                font-size: 14px;
                color: #0F172A;
            }
            QLineEdit:focus {
                border: 2px solid #2563EB;
                padding: 11.5px 15.5px;
            }
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                gridline-color: #F1F5F9;
                font-size: 14px;
                color: #0F172A;
                selection-background-color: #EFF6FF;
                selection-color: #1D4ED8;
                alternate-background-color: #FAFBFD;
            }
            QTableWidget::item {
                padding: 14px 10px;
                border-bottom: 1px solid #F1F5F9;
            }
            QTableWidget::item:selected {
                background-color: #EFF6FF;
                color: #1D4ED8;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                padding: 16px 10px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: 700;
                font-size: 13px;
            }
            QProgressBar {
                background-color: #E2E8F0;
                border: none;
                border-radius: 4px;
                height: 8px;
            }
            QProgressBar::chunk {
                background-color: #2563EB;
                border-radius: 4px;
            }
        """)

    # ------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------
    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        main_layout.addLayout(self.build_header())
        main_layout.addLayout(self.build_stats_section())
        main_layout.addLayout(self.build_controls_section())
        main_layout.addWidget(self.build_loading_bar())
        main_layout.addWidget(self.build_table())
        main_layout.addLayout(self.build_status_bar())

    def build_header(self):
        header_layout = QVBoxLayout()
        header_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header_layout.setSpacing(6)

        title_label = QLabel(
            "Association de la Jeunesse d'Idourhamane pour le Développement et la Coopération"
        )
        title_label.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel("Système de Facturation d'Eau et de Gestion des Factures")
        subtitle_label.setStyleSheet(
            "font-size: 15px; color: #64748B; font-weight: 500;"
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header_layout.addWidget(title_label)
        header_layout.addWidget(subtitle_label)
        return header_layout

    def build_stats_section(self):
        """Simple stats row — no cards, no borders, just clean numbers."""
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(40)
        stats_layout.setContentsMargins(0, 12, 0, 12)

        stats_data = [
            ("Tous les utilisateurs", "—", "#2563EB"),
            ("Utilisateurs payés", "—", "#22C55E"),
            ("Utilisateurs impayés", "—", "#EF4444"),
        ]

        self.stat_labels = {}
        for title, value, color in stats_data:
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            v_label = QLabel(value)
            v_label.setStyleSheet(
                f"font-size: 36px; font-weight: 700; color: {color}; letter-spacing: -1px;"
            )
            v_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self.stat_labels[title] = v_label

            t_label = QLabel(title)
            t_label.setStyleSheet("font-size: 13px; color: #64748B; font-weight: 500;")
            t_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

            col.addWidget(v_label)
            col.addWidget(t_label)
            stats_layout.addLayout(col)

        return stats_layout

    def build_controls_section(self):
        """Simple controls row — no card frame."""
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 8, 0, 8)

        self.btn_show_all = QPushButton("Afficher tous les utilisateurs")
        self.btn_show_all.setProperty("class", "action-btn")
        self.btn_show_all.setMinimumHeight(44)
        self.btn_show_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_all.clicked.connect(self.show_all_users_view)

        self.btn_show_paid = QPushButton("Afficher les utilisateurs payés")
        self.btn_show_paid.setProperty("class", "action-btn")
        self.btn_show_paid.setMinimumHeight(44)
        self.btn_show_paid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_paid.clicked.connect(self.show_paid_users_view)

        self.btn_generate_invoices = QPushButton("Générer toutes les factures des utilisateurs payés")
        self.btn_generate_invoices.setProperty("class", "primary-btn")
        self.btn_generate_invoices.setMinimumHeight(44)
        self.btn_generate_invoices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_invoices.clicked.connect(self.handle_generate_invoices)
        self.btn_generate_invoices.hide()

        layout.addWidget(self.btn_show_all)
        layout.addWidget(self.btn_show_paid)
        layout.addStretch()
        layout.addWidget(self.btn_generate_invoices)

        # Search + refresh + settings on a second row
        search_row = QHBoxLayout()
        search_row.setSpacing(12)
        search_row.setContentsMargins(0, 8, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher par numéro de compteur ou nom..."
        )
        self.search_input.setMinimumHeight(44)
        self.search_input.textChanged.connect(self.filter_table)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setProperty("class", "action-btn")
        self.btn_refresh.setMinimumHeight(44)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_data_from_api)

        self.btn_settings = QPushButton("Paramètres")
        self.btn_settings.setProperty("class", "action-btn")
        self.btn_settings.setMinimumHeight(44)
        self.btn_settings.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_settings.clicked.connect(self.open_settings_dialog)

        search_row.addWidget(self.search_input, stretch=1)
        search_row.addWidget(self.btn_refresh)
        search_row.addWidget(self.btn_settings)

        combined = QVBoxLayout()
        combined.addLayout(layout)
        combined.addLayout(search_row)
        return combined

    def build_loading_bar(self):
        self.loading_bar = QProgressBar()
        self.loading_bar.setMinimum(0)
        self.loading_bar.setMaximum(0)
        self.loading_bar.setTextVisible(False)
        self.loading_bar.setFixedHeight(4)
        self.loading_bar.hide()
        return self.loading_bar

    def build_table(self):
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            [
                "Numéro de compteur",
                "Nom complet",
                "Ancienne lecture",
                "Lecture actuelle",
                "Consommation",
                "Montant de la facture",
                "Statut",
            ]
        )
        self.table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.verticalHeader().setDefaultSectionSize(52)
        return self.table

    def build_status_bar(self):
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(4, 4, 4, 0)

        self.dot = QLabel("●")
        self.dot.setStyleSheet("font-size: 11px; color: #22C55E;")

        self.status_label = QLabel("Connexion au serveur...")
        self.status_label.setStyleSheet(
            "font-size: 13px; color: #334155; font-weight: 600;"
        )

        version_label = QLabel("v1.0.0 — Édition Bureau")
        version_label.setStyleSheet("font-size: 12px; color: #94A3B8;")

        status_layout.addWidget(self.dot)
        status_layout.addSpacing(6)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(version_label)

        return status_layout

    # ------------------------------------------------------------------
    # API & THREADING INTEGRATION
    # ------------------------------------------------------------------
    def load_data_from_api(self):
        self.set_loading_state(True)
        self.worker = FetchUsersWorker()
        self.worker.finished.connect(self.handle_data_received)
        self.worker.start()

    def set_loading_state(self, is_loading):
        if is_loading:
            self.loading_bar.show()
            self.status_label.setText("Récupération des données du serveur...")
            self.btn_show_all.setEnabled(False)
            self.btn_show_paid.setEnabled(False)
            self.btn_generate_invoices.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.btn_settings.setEnabled(False)
            self.search_input.setEnabled(False)
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 7)
            placeholder = QTableWidgetItem("Chargement des données, veuillez patienter...")
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            font = QFont("Segoe UI", 14)
            font.setWeight(QFont.Weight.Medium)
            placeholder.setFont(font)
            placeholder.setForeground(QColor("#94A3B8"))
            self.table.setItem(0, 0, placeholder)
        else:
            self.loading_bar.hide()
            self.btn_show_all.setEnabled(True)
            self.btn_show_paid.setEnabled(True)
            self.btn_generate_invoices.setEnabled(True)
            self.btn_refresh.setEnabled(True)
            self.btn_settings.setEnabled(True)
            self.search_input.setEnabled(True)

    def handle_data_received(self, data, error):
        if error:
            self.set_loading_state(False)
            self.dot.setStyleSheet("font-size: 11px; color: #EF4444;")
            self.status_label.setText(f"Erreur de connexion : {error}")
            self.table.setRowCount(0)
            return

        if isinstance(data, dict):
            if not data.get("success", True):
                self.set_loading_state(False)
                self.dot.setStyleSheet("font-size: 11px; color: #EF4444;")
                self.status_label.setText(
                    f"Erreur API : {data.get('error', 'Erreur inconnue')}"
                )
                self.table.setRowCount(0)
                return
            records = data.get("data", [])
        elif isinstance(data, list):
            records = data
        else:
            records = []

        self.dot.setStyleSheet("font-size: 11px; color: #22C55E;")
        self.status_label.setText("Backend connecté  |  WhatsApp connecté  |  Prêt")

        formatted_rows = []
        for item in records:
            if isinstance(item, dict):
                is_paid = bool(item.get("isPaid", False))
                status = "Payé" if is_paid else "Impayé"
                consumption = item.get("consumptionM3", item.get("consumption", 0))
                bill = item.get("totalBill", 0)

                row = (
                    str(item.get("meterNumber", "")),
                    str(item.get("fullName", "")),
                    str(item.get("previousReading", 0)),
                    str(item.get("currentReading", 0)),
                    f"{consumption} m3",
                    f"{bill} MAD",
                    status,
                )
            else:
                row = tuple(str(x) for x in item)
            formatted_rows.append(row)

        self.raw_data = formatted_rows
        self.api_records = records
        self.set_loading_state(False)
        self.update_statistics()
        self.show_all_users_view()

    def update_statistics(self):
        total_count = len(self.raw_data)
        paid_count = sum(1 for row in self.raw_data if row[6] == "Payé")
        unpaid_count = total_count - paid_count

        if "Tous les utilisateurs" in self.stat_labels:
            self.stat_labels["Tous les utilisateurs"].setText(f"{total_count:,}")
        if "Utilisateurs payés" in self.stat_labels:
            self.stat_labels["Utilisateurs payés"].setText(f"{paid_count:,}")
        if "Utilisateurs impayés" in self.stat_labels:
            self.stat_labels["Utilisateurs impayés"].setText(f"{unpaid_count:,}")

    # ------------------------------------------------------------------
    # DATA / VIEW LOGIC
    # ------------------------------------------------------------------
    def get_active_source_data(self):
        if self.current_view == "paid":
            return [row for row in self.raw_data if row[6] == "Payé"]
        return self.raw_data

    def populate_table(self, data_rows):
        self.table.setRowCount(len(data_rows))
        for row_idx, row_data in enumerate(data_rows):
            for col_idx, text in enumerate(row_data):
                if col_idx == 6:
                    badge_widget = QWidget()
                    badge_layout = QHBoxLayout(badge_widget)
                    badge_layout.setContentsMargins(10, 6, 10, 6)
                    badge_label = QLabel(text)
                    badge_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    font = QFont()
                    font.setBold(True)
                    font.setPointSize(11)
                    badge_label.setFont(font)

                    if text == "Payé":
                        badge_label.setStyleSheet(
                            "color: #166534; background-color: #DCFCE7; "
                            "border-radius: 8px; padding: 6px 16px; font-weight: 700; font-size: 12px;"
                        )
                    elif text == "En attente":
                        badge_label.setStyleSheet(
                            "color: #92400E; background-color: #FEF3C7; "
                            "border-radius: 8px; padding: 6px 16px; font-weight: 700; font-size: 12px;"
                        )
                    else:
                        badge_label.setStyleSheet(
                            "color: #991B1B; background-color: #FEE2E2; "
                            "border-radius: 8px; padding: 6px 16px; font-weight: 700; font-size: 12px;"
                        )

                    badge_layout.addWidget(badge_label)
                    badge_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    self.table.setCellWidget(row_idx, col_idx, badge_widget)
                else:
                    item = QTableWidgetItem(text)
                    align = (
                        Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
                        if col_idx == 1
                        else Qt.AlignmentFlag.AlignCenter
                    )
                    item.setTextAlignment(align)
                    self.table.setItem(row_idx, col_idx, item)

    def filter_table(self):
        query = self.search_input.text().strip().lower()
        source_data = self.get_active_source_data()

        if not query:
            filtered_data = source_data
        else:
            filtered_data = [
                row
                for row in source_data
                if query in row[0].lower() or query in row[1].lower()
            ]

        self.populate_table(filtered_data)

    def _set_toggle_state(self, active_btn, inactive_btn):
        active_btn.setProperty("class", "action-btn-active")
        inactive_btn.setProperty("class", "action-btn")
        for btn in (active_btn, inactive_btn):
            btn.style().unpolish(btn)
            btn.style().polish(btn)

    def show_all_users_view(self):
        self.current_view = "all"
        self._set_toggle_state(self.btn_show_all, self.btn_show_paid)
        self.btn_generate_invoices.hide()
        self.search_input.clear()
        self.populate_table(self.raw_data)

    def show_paid_users_view(self):
        self.current_view = "paid"
        self._set_toggle_state(self.btn_show_paid, self.btn_show_all)
        self.btn_generate_invoices.show()
        self.search_input.clear()
        paid_data = [row for row in self.raw_data if row[6] == "Payé"]
        self.populate_table(paid_data)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data_from_api()

    def handle_generate_invoices(self):
        paid_users = [
            record for record in self.api_records
            if bool(record.get("isPaid", False))
        ]

        if not paid_users:
            CustomMessageBox.warning(
                self,
                "Aucun utilisateur payé",
                "Il n'y a pas d'utilisateurs payés pour lesquels générer des factures.",
            )
            return

        progress = InvoiceProgressDialog(len(paid_users), self)
        progress.show()
        QApplication.processEvents()

        try:
            generator = Generator(paid_users)

            total = len(paid_users)
            for i in range(total):
                if progress.wasCanceled():
                    break
                user_name = paid_users[i].get("fullName", f"Utilisateur {i+1}")
                progress.update_progress(i, user_name)

            if not progress.wasCanceled():
                generator.generate_bills()
                progress.update_progress(total, "Terminé !")

        except GeneratorError as e:
            progress.close()
            CustomMessageBox.critical(
                self,
                "Échec de la génération des factures",
                f"Impossible de générer les factures :\n{e}",
            )
            return

        progress.close()
        if not progress.wasCanceled():
            CustomMessageBox.info(
                self,
                "Factures générées",
                f"Factures générées avec succès pour {len(paid_users)} utilisateurs payés.\n\n"
                f"Une file d'attente d'envoi WhatsApp (whatsapp_queue.json) a également été créée "
                f"dans le dossier de sauvegarde pour l'extension Chrome.",
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WaterAssociationApp()
    window.show()
    sys.exit(app.exec())