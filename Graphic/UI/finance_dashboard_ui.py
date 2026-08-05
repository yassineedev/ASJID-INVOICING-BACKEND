"""
finance_dashboard.py — Tableau de bord Financier & Recouvrement ASJID

Shows:
  • Financial summary KPIs (Total billed, collected, remaining, collection rate)
  • Configurable price per m³ tariff control
  • Household billing & payment status tracker
  • Search & filter capabilities
  • High performance native rendering
"""

from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QFrame, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QGraphicsDropShadowEffect, QDoubleSpinBox,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QLinearGradient


# ═══════════════════════════════════════════════════════════════════════════
#  MINI WIDGETS
# ═══════════════════════════════════════════════════════════════════════════

class FinanceKpiCard(QFrame):
    """Small metric card for financial values."""

    def __init__(self, value, label, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(220, 100)
        self.setStyleSheet("""
            FinanceKpiCard {
                background-color: #FFFFFF;
                border-radius: 16px;
                border: 1px solid #E2E8F0;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(20)
        shadow.setColor(QColor(0, 0, 0, 12))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        v = QLabel(value)
        v.setStyleSheet("font-size: 24px; font-weight: 800; color: %s; letter-spacing: -0.5px;" % color)

        l = QLabel(label)
        l.setStyleSheet("font-size: 11px; font-weight: 600; color: #94A3B8; letter-spacing: 0.5px;")

        layout.addWidget(v)
        layout.addWidget(l)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN FINANCE DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

class FinanceDashboard(QWidget):
    """
    Financial management and billing dashboard for tracking expected revenue, 
    collected payments, and household balances.

    Signals:
        back_signal.emit()         → Request return to Home page
        request_refresh_signal()   → Request parent to refresh data
    """

    back_signal = Signal()
    request_refresh_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []          # Normalized records
        self._filtered = []      # Filtered records
        self.init_ui()

    # ── UI Construction ──

    def init_ui(self):
        self.setStyleSheet("""
            FinanceDashboard {
                background-color: #F8FAFC;
            }
            QLabel {
                font-family: 'Segoe UI', 'SF Pro Display', -apple-system, sans-serif;
                color: #0F172A;
            }
            QLineEdit, QDoubleSpinBox {
                background-color: #FFFFFF;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 8px 12px;
                font-size: 14px;
                color: #0F172A;
            }
            QLineEdit:focus, QDoubleSpinBox:focus {
                border: 2px solid #2563EB;
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
                padding: 12px 10px;
                border-bottom: 1px solid #F1F5F9;
            }
            QHeaderView::section {
                background-color: #F8FAFC;
                color: #64748B;
                padding: 14px 10px;
                border: none;
                border-bottom: 2px solid #E2E8F0;
                font-weight: 700;
                font-size: 12px;
                letter-spacing: 0.5px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(24)

        # ── Header row ──
        header = QHBoxLayout()
        header.setSpacing(16)

        self._btn_back = QPushButton("←  Retour")
        self._btn_back.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_back.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #64748B;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 10px 18px;
                font-size: 14px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F1F5F9;
                color: #334155;
            }
        """)
        self._btn_back.clicked.connect(self.back_signal.emit)

        self._title = QLabel("Gestion Financière & Recouvrement")
        self._title.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.3px;
        """)

        self._month_label = QLabel("Budget: Juillet 2026")
        self._month_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #059669;
            background-color: #ECFDF5;
            border-radius: 8px;
            padding: 6px 14px;
        """)

        header.addWidget(self._btn_back)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._month_label)

        layout.addLayout(header)

        # ── Financial KPI Cards row ──
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        kpi_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._kpi_billed = FinanceKpiCard("—", "MONTANT TOTAL FACTURÉ", "#2563EB")
        self._kpi_collected = FinanceKpiCard("—", "TOTAL ENCAISSÉ", "#059669")
        self._kpi_remaining = FinanceKpiCard("—", "RESTE À RECOUVRER", "#DC2626")
        self._kpi_rate = FinanceKpiCard("—", "TAUX DE RECOUVREMENT", "#7C3AED")

        kpi_row.addWidget(self._kpi_billed)
        kpi_row.addWidget(self._kpi_collected)
        kpi_row.addWidget(self._kpi_remaining)
        kpi_row.addWidget(self._kpi_rate)
        kpi_row.addStretch()

        layout.addLayout(kpi_row)

        # ── Toolbar ──
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Rechercher par nom ou numéro de compteur...")
        self._search.setMinimumHeight(42)
        self._search.textChanged.connect(self._on_search)

        # Tariff Control Container
        tariff_container = QHBoxLayout()
        tariff_container.setSpacing(6)
        
        lbl_tariff = QLabel("Tarif / m³ (DH):")
        lbl_tariff.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569;")

        self._tariff_spin = QDoubleSpinBox()
        self._tariff_spin.setRange(1.0, 50.0)
        self._tariff_spin.setSingleStep(0.5)
        self._tariff_spin.setValue(5.0)  # Default price per m³
        self._tariff_spin.setMinimumHeight(42)
        self._tariff_spin.setFixedWidth(85)
        self._tariff_spin.valueChanged.connect(self._on_tariff_changed)

        tariff_container.addWidget(lbl_tariff)
        tariff_container.addWidget(self._tariff_spin)

        self._btn_refresh = QPushButton("↻  Actualiser")
        self._btn_refresh.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_refresh.setMinimumHeight(42)
        self._btn_refresh.setStyleSheet("""
            QPushButton {
                background-color: #FFFFFF;
                color: #334155;
                border: 1.5px solid #E2E8F0;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #F8FAFC;
                border-color: #CBD5E1;
            }
        """)
        self._btn_refresh.clicked.connect(self.request_refresh_signal.emit)

        self._btn_export = QPushButton("⬇  Exporter Bilan")
        self._btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export.setMinimumHeight(42)
        self._btn_export.setStyleSheet("""
            QPushButton {
                background-color: #059669;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #047857; }
        """)

        toolbar.addWidget(self._search, stretch=1)
        toolbar.addLayout(tariff_container)
        toolbar.addWidget(self._btn_refresh)
        toolbar.addWidget(self._btn_export)

        layout.addLayout(toolbar)

        # ── Table ──
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "COMPTEUR", "NOM DU CLIENT", "CONSOMMATION", "PRIX / m³", "MONTANT TOTAL", "STATUT DE PAIEMENT"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 100)
        self._table.setColumnWidth(3, 110)
        self._table.setColumnWidth(5, 170)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setDefaultSectionSize(48)

        layout.addWidget(self._table)

        # ── Footer ──
        footer = QHBoxLayout()
        self._status = QLabel("En attente des données financières...")
        self._status.setStyleSheet("font-size: 12px; color: #94A3B8;")
        footer.addWidget(self._status)
        footer.addStretch()
        layout.addLayout(footer)

    # ── Data Handling & Calculations ──

    def set_data(self, records):
        """Loads records and prepares financial records."""
        normalized_records = []
        for item in records:
            if not isinstance(item, dict):
                continue
            
            meter = str(
                item.get("meterNumber") or item.get("meter") or 
                item.get("Compteur") or item.get("numero") or ""
            )
            name = str(
                item.get("fullName") or item.get("name") or 
                item.get("Nom") or item.get("client") or ""
            )
            
            raw_cons = (
                item.get("consumptionM3") or item.get("consumption") or 
                item.get("consommation") or item.get("current") or 0.0
            )
            try:
                cons = float(raw_cons)
            except (ValueError, TypeError):
                cons = 0.0

            if cons < 0:
                cons = 0.0

            is_paid = bool(item.get("isPaid", item.get("paid", False)))

            normalized_records.append({
                "meterNumber": meter,
                "fullName": name,
                "consumptionM3": cons,
                "isPaid": is_paid
            })

        self._data = normalized_records
        self._filtered = self._data[:]
        self._compute_financial_stats()
        self._populate_table()
        self._status.setText("Bilan financier synchronisé — %d abonnés" % len(self._data))

    def _compute_financial_stats(self):
        if not self._data:
            self._kpi_billed.layout().itemAt(0).widget().setText("0.00 DH")
            self._kpi_collected.layout().itemAt(0).widget().setText("0.00 DH")
            self._kpi_remaining.layout().itemAt(0).widget().setText("0.00 DH")
            self._kpi_rate.layout().itemAt(0).widget().setText("0%")
            return

        tariff = self._tariff_spin.value()
        total_billed = sum(r["consumptionM3"] * tariff for r in self._data)
        total_collected = sum(r["consumptionM3"] * tariff for r in self._data if r["isPaid"])
        remaining = total_billed - total_collected
        rate = (total_collected / total_billed * 100) if total_billed > 0 else 0.0

        self._kpi_billed.layout().itemAt(0).widget().setText("%.2f DH" % total_billed)
        self._kpi_collected.layout().itemAt(0).widget().setText("%.2f DH" % total_collected)
        self._kpi_remaining.layout().itemAt(0).widget().setText("%.2f DH" % remaining)
        self._kpi_rate.layout().itemAt(0).widget().setText("%.1f%%" % rate)

    def _on_search(self):
        query = self._search.text().strip().lower()
        if not query:
            self._filtered = self._data[:]
        else:
            self._filtered = [
                r for r in self._data
                if query in str(r.get("fullName", "")).lower()
                or query in str(r.get("meterNumber", "")).lower()
            ]
        self._populate_table()

    def _on_tariff_changed(self, value):
        self._compute_financial_stats()
        self._populate_table()

    def _populate_table(self):
        """Populates the billing table with lightning-fast native item rendering."""
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(len(self._filtered))

        tariff = self._tariff_spin.value()

        for i, record in enumerate(self._filtered):
            meter = str(record.get("meterNumber", ""))
            name = str(record.get("fullName", ""))
            cons = float(record.get("consumptionM3", 0.0))
            is_paid = record.get("isPaid", False)
            amount = cons * tariff

            # 1. Meter
            item_meter = QTableWidgetItem(meter)
            item_meter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_meter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            self._table.setItem(i, 0, item_meter)

            # 2. Name
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 1, item_name)

            # 3. Consumption
            item_cons = QTableWidgetItem("%.1f m³" % cons)
            item_cons.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 2, item_cons)

            # 4. Tariff unit
            item_tariff = QTableWidgetItem("%.2f DH" % tariff)
            item_tariff.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(i, 3, item_tariff)

            # 5. Total Amount
            item_amount = QTableWidgetItem("%.2f DH" % amount)
            item_amount.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_amount.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            item_amount.setForeground(QColor("#2563EB"))
            self._table.setItem(i, 4, item_amount)

            # 6. Payment Status
            status_text = "🟢 Payé" if is_paid else "🔴 Impayé"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_status.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
            if is_paid:
                item_status.setForeground(QColor("#166534"))
            else:
                item_status.setForeground(QColor("#991B1B"))
            self._table.setItem(i, 5, item_status)

        self._table.setUpdatesEnabled(True)

    def _render_table(self):
        self._populate_table()  