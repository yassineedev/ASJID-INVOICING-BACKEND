# views/billing_view.py
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QProgressBar,
    QDialog,
    QApplication,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from workers import FetchUsersWorker
from invoice import Generator, GeneratorError
from settings_dialog import SettingsDialog
from dialogs import CustomMessageBox, InvoiceProgressDialog


class BillingView(QWidget):
    navigate_signal = Signal(int)

    def __init__(self):
        super().__init__()
        self.raw_data = []
        self.api_records = []
        self.current_view = "all"

        self.init_ui()
        self.load_data_from_api()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(32, 28, 32, 28)
        main_layout.setSpacing(24)

        main_layout.addLayout(self.build_header())
        main_layout.addLayout(self.build_stats_section())
        main_layout.addLayout(self.build_controls_section())
        main_layout.addWidget(self.build_loading_bar())
        main_layout.addWidget(self.build_table())
        main_layout.addLayout(self.build_status_bar())

    def build_header(self):
        header_layout = QHBoxLayout()

        back_btn = QPushButton("← Back to Home")
        back_btn.setFixedWidth(140)
        back_btn.setCursor(Qt.PointingHandCursor)
        back_btn.setStyleSheet("""
            QPushButton {
                background-color: #F8FAFC; color: #334155; border: 1.5px solid #E2E8F0;
                border-radius: 8px; padding: 8px 14px; font-weight: 600; font-size: 13px;
            }
            QPushButton:hover { background-color: #F1F5F9; border-color: #CBD5E1; }
        """)
        back_btn.clicked.connect(lambda: self.navigate_signal.emit(0))

        titles_col = QVBoxLayout()
        titles_col.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles_col.setSpacing(4)

        title_label = QLabel(
            "Association de la Jeunesse d'Idourhamane pour le Developpement et la Cooperation"
        )
        title_label.setStyleSheet("font-size: 20px; font-weight: 700; color: #0F172A;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        subtitle_label = QLabel(
            "Systeme de Facturation d'Eau et de Gestion des Factures"
        )
        subtitle_label.setStyleSheet(
            "font-size: 14px; color: #64748B; font-weight: 500;"
        )
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        titles_col.addWidget(title_label)
        titles_col.addWidget(subtitle_label)

        header_layout.addWidget(back_btn, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        header_layout.addLayout(titles_col)
        header_layout.addStretch()

        return header_layout

    def build_stats_section(self):
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(40)
        stats_layout.setContentsMargins(0, 8, 0, 8)

        stats_data = [
            ("Tous les utilisateurs", "-", "#2563EB"),
            ("Utilisateurs payes", "-", "#22C55E"),
            ("Utilisateurs impayes", "-", "#EF4444"),
        ]

        self.stat_labels = {}
        for title, value, color in stats_data:
            col = QVBoxLayout()
            col.setSpacing(4)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)

            v_label = QLabel(value)
            v_label.setStyleSheet(
                "font-size: 32px; font-weight: 700; color: %s; letter-spacing: -1px;"
                % color
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
        layout = QHBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(0, 4, 0, 4)

        self.btn_show_all = QPushButton("Afficher tous les utilisateurs")
        self.btn_show_all.setProperty("class", "action-btn")
        self.btn_show_all.setMinimumHeight(42)
        self.btn_show_all.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_all.clicked.connect(self.show_all_users_view)

        self.btn_show_paid = QPushButton("Afficher les utilisateurs payes")
        self.btn_show_paid.setProperty("class", "action-btn")
        self.btn_show_paid.setMinimumHeight(42)
        self.btn_show_paid.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_show_paid.clicked.connect(self.show_paid_users_view)

        self.btn_generate_invoices = QPushButton(
            "Generer toutes les factures des utilisateurs payes"
        )
        self.btn_generate_invoices.setProperty("class", "primary-btn")
        self.btn_generate_invoices.setMinimumHeight(42)
        self.btn_generate_invoices.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_generate_invoices.clicked.connect(self.handle_generate_invoices)
        self.btn_generate_invoices.hide()

        layout.addWidget(self.btn_show_all)
        layout.addWidget(self.btn_show_paid)
        layout.addStretch()
        layout.addWidget(self.btn_generate_invoices)

        search_row = QHBoxLayout()
        search_row.setSpacing(12)
        search_row.setContentsMargins(0, 4, 0, 0)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText(
            "Rechercher par numero de compteur ou nom..."
        )
        self.search_input.setMinimumHeight(42)
        self.search_input.textChanged.connect(self.filter_table)

        self.btn_refresh = QPushButton("Actualiser")
        self.btn_refresh.setProperty("class", "action-btn")
        self.btn_refresh.setMinimumHeight(42)
        self.btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_refresh.clicked.connect(self.load_data_from_api)

        self.btn_settings = QPushButton("Parametres")
        self.btn_settings.setProperty("class", "action-btn")
        self.btn_settings.setMinimumHeight(42)
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
                "Numero de compteur",
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
        self.table.verticalHeader().setDefaultSectionSize(48)
        return self.table

    def build_status_bar(self):
        status_layout = QHBoxLayout()
        status_layout.setContentsMargins(4, 2, 4, 0)

        self.dot = QLabel("*")
        self.dot.setStyleSheet("font-size: 11px; color: #22C55E;")

        self.status_label = QLabel("Connexion au serveur...")
        self.status_label.setStyleSheet(
            "font-size: 13px; color: #334155; font-weight: 600;"
        )

        status_layout.addWidget(self.dot)
        status_layout.addSpacing(6)
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()

        return status_layout

    def load_data_from_api(self):
        self.set_loading_state(True)
        self.worker = FetchUsersWorker()
        self.worker.finished.connect(self.handle_data_received)
        self.worker.start()

    def set_loading_state(self, is_loading):
        if is_loading:
            self.loading_bar.show()
            self.status_label.setText("Recuperation des donnees du serveur...")
            self.btn_show_all.setEnabled(False)
            self.btn_show_paid.setEnabled(False)
            self.btn_generate_invoices.setEnabled(False)
            self.btn_refresh.setEnabled(False)
            self.btn_settings.setEnabled(False)
            self.search_input.setEnabled(False)
            self.table.setRowCount(1)
            self.table.setSpan(0, 0, 1, 7)
            placeholder = QTableWidgetItem(
                "Chargement des donnees, veuillez patienter..."
            )
            placeholder.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            font = QFont("Segoe UI", 13)
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
            self.status_label.setText("Erreur de connexion : %s" % error)
            self.table.setRowCount(0)
            return

        if isinstance(data, dict):
            if not data.get("success", True):
                self.set_loading_state(False)
                self.dot.setStyleSheet("font-size: 11px; color: #EF4444;")
                self.status_label.setText(
                    "Erreur API : %s" % data.get("error", "Erreur inconnue")
                )
                self.table.setRowCount(0)
                return
            records = data.get("data", [])
        elif isinstance(data, list):
            records = data
        else:
            records = []

        self.dot.setStyleSheet("font-size: 11px; color: #22C55E;")
        self.status_label.setText("Backend connecte  |  WhatsApp connecte  |  Pret")

        formatted_rows = []
        for item in records:
            if isinstance(item, dict):
                is_paid = bool(item.get("isPaid", False))
                status = "Paye" if is_paid else "Impaye"
                consumption = item.get("consumptionM3", item.get("consumption", 0))
                bill = item.get("totalBill", 0)

                row = (
                    str(item.get("meterNumber", "")),
                    str(item.get("fullName", "")),
                    str(item.get("previousReading", 0)),
                    str(item.get("currentReading", 0)),
                    "%s m3" % consumption,
                    "%s MAD" % bill,
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
        paid_count = sum(1 for row in self.raw_data if row[6] == "Paye")
        unpaid_count = total_count - paid_count

        if "Tous les utilisateurs" in self.stat_labels:
            self.stat_labels["Tous les utilisateurs"].setText("%d" % total_count)
        if "Utilisateurs payes" in self.stat_labels:
            self.stat_labels["Utilisateurs payes"].setText("%d" % paid_count)
        if "Utilisateurs impayes" in self.stat_labels:
            self.stat_labels["Utilisateurs impayes"].setText("%d" % unpaid_count)

    def get_active_source_data(self):
        if self.current_view == "paid":
            return [row for row in self.raw_data if row[6] == "Paye"]
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

                    if text == "Paye":
                        badge_label.setStyleSheet(
                            "color: #166534; background-color: #DCFCE7; border-radius: 8px; padding: 4px 12px; font-weight: 700; font-size: 12px;"
                        )
                    else:
                        badge_label.setStyleSheet(
                            "color: #991B1B; background-color: #FEE2E2; border-radius: 8px; padding: 4px 12px; font-weight: 700; font-size: 12px;"
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
        paid_data = [row for row in self.raw_data if row[6] == "Paye"]
        self.populate_table(paid_data)

    def open_settings_dialog(self):
        dialog = SettingsDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.load_data_from_api()

    def handle_generate_invoices(self):
        paid_users = [
            record for record in self.api_records if bool(record.get("isPaid", False))
        ]
        if not paid_users:
            CustomMessageBox.warning(
                self,
                "Aucun utilisateur paye",
                "Il n'y a pas d'utilisateurs payes pour lesquels generer des factures.",
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
                user_name = paid_users[i].get("fullName", "Utilisateur %d" % (i + 1))
                progress.update_progress(i, user_name)

            if not progress.wasCanceled():
                generator.generate_bills()
                progress.update_progress(total, "Termine !")
        except GeneratorError as e:
            progress.close()
            CustomMessageBox.critical(
                self, "Echec", "Impossible de generer les factures : %s" % e
            )
            return

        progress.close()
        if not progress.wasCanceled():
            CustomMessageBox.info(
                self,
                "Factures generees",
                "Factures generees avec succes pour %d utilisateurs payes."
                % len(paid_users),
            )
