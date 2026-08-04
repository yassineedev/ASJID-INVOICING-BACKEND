"""
consumption_dashboard.py — Tableau de bord Consommation ASJID

Rebuilt analytical logic for real-world village water management:
  • Ranked highest-to-lowest consumers for immediate anomaly spotting
  • Practical volume-based thresholds (in m³) instead of confusing ratios
  • Clear operational alert statuses (Leaks, High usage, Normal, Inactive)
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

class KpiCard(QFrame):
    def __init__(self, value, label, color, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        self.setStyleSheet("""
            KpiCard {
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
        v.setStyleSheet("font-size: 26px; font-weight: 800; color: %s; letter-spacing: -0.5px;" % color)

        l = QLabel(label)
        l.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; letter-spacing: 0.5px;")

        layout.addWidget(v)
        layout.addWidget(l)


class RankBadge(QWidget):
    def __init__(self, rank, size=32, parent=None):
        super().__init__(parent)
        self.rank = rank
        self.setFixedSize(size, size)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        colors = {
            1: ("#F59E0B", "#FFFFFF"),   # Gold
            2: ("#94A3B8", "#FFFFFF"),   # Silver
            3: ("#B45309", "#FFFFFF"),   # Bronze
        }
        bg, fg = colors.get(self.rank, ("#E2E8F0", "#64748B"))

        painter.setBrush(QBrush(QColor(bg)))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect())

        painter.setPen(QPen(QColor(fg)))
        painter.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, str(self.rank))


class ConsumptionBar(QWidget):
    def __init__(self, value, max_value, color="#2563EB", parent=None):
        super().__init__(parent)
        self.value = value
        self.max_value = max_value
        self.color = color
        self.setFixedHeight(8)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QBrush(QColor("#E2E8F0")))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(self.rect(), 4, 4)

        if self.max_value <= 0:
            return

        ratio = min(self.value / self.max_value, 1.0)
        bar_w = int(self.width() * ratio)
        if bar_w < 2:
            return

        grad = QLinearGradient(0, 0, bar_w, 0)
        grad.setColorAt(0.0, QColor(self.color))
        grad.setColorAt(1.0, QColor(self._lighten(self.color)))

        painter.setBrush(QBrush(grad))
        painter.drawRoundedRect(0, 0, bar_w, self.height(), 4, 4)

    def _lighten(self, hex_color):
        c = QColor(hex_color)
        h, s, l, a = c.getHsl()
        return QColor.fromHsl(h, s, min(l + 20, 255), a).name()


class AlertPill(QWidget):
    def __init__(self, text, bg, fg, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 2, 8, 2)
        layout.setSpacing(0)

        lbl = QLabel(text)
        lbl.setStyleSheet("""
            font-size: 11px;
            font-weight: 700;
            color: %s;
            background-color: %s;
            border-radius: 6px;
            padding: 3px 10px;
        """ % (fg, bg))
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)


# ═══════════════════════════════════════════════════════════════════════════
#  MAIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════

class ConsumptionDashboard(QWidget):
    back_signal = Signal()
    request_refresh_signal = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data = []          
        self._filtered = []      
        self._max_consumption = 1.0
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet("""
            ConsumptionDashboard {
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

        # Header row
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

        self._title = QLabel("Tableau de bord Consommation")
        self._title.setStyleSheet("""
            font-size: 24px;
            font-weight: 800;
            color: #0F172A;
            letter-spacing: -0.3px;
        """)

        self._month_label = QLabel("Mois: Juillet 2026")
        self._month_label.setStyleSheet("""
            font-size: 13px;
            font-weight: 600;
            color: #3B82F6;
            background-color: #EFF6FF;
            border-radius: 8px;
            padding: 6px 14px;
        """)

        header.addWidget(self._btn_back)
        header.addWidget(self._title)
        header.addStretch()
        header.addWidget(self._month_label)

        layout.addLayout(header)

        # KPI Cards row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(16)
        kpi_row.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self._kpi_total = KpiCard("—", "CONSOMMATION TOTALE", "#2563EB")
        self._kpi_avg = KpiCard("—", "MOYENNE / COMPTEUR", "#059669")
        self._kpi_max = KpiCard("—", "MAXIMUM ENREGISTRÉ", "#DC2626")
        self._kpi_active = KpiCard("—", "COMPTEURS ACTIFS", "#7C3AED")

        kpi_row.addWidget(self._kpi_total)
        kpi_row.addWidget(self._kpi_avg)
        kpi_row.addWidget(self._kpi_max)
        kpi_row.addWidget(self._kpi_active)
        kpi_row.addStretch()

        layout.addLayout(kpi_row)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        self._search = QLineEdit()
        self._search.setPlaceholderText("🔍  Rechercher par nom ou numéro de compteur...")
        self._search.setMinimumHeight(42)
        self._search.textChanged.connect(self._on_search)

        # Rebuilt control: Absolute Volume Threshold instead of an abstract ratio
        threshold_container = QHBoxLayout()
        threshold_container.setSpacing(6)
        
        lbl_threshold = QLabel("Seuil Alerte (m³):")
        lbl_threshold.setStyleSheet("font-size: 13px; font-weight: 600; color: #475569;")

        self._threshold_spin = QDoubleSpinBox()
        self._threshold_spin.setRange(5.0, 100.0)
        self._threshold_spin.setSingleStep(1.0)
        self._threshold_spin.setValue(20.0)  # 20 m³ standard warning limit
        self._threshold_spin.setMinimumHeight(42)
        self._threshold_spin.setFixedWidth(85)
        self._threshold_spin.valueChanged.connect(self._on_threshold_changed)

        threshold_container.addWidget(lbl_threshold)
        threshold_container.addWidget(self._threshold_spin)

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

        self._btn_export = QPushButton("⬇  Exporter")
        self._btn_export.setCursor(Qt.CursorShape.PointingHandCursor)
        self._btn_export.setMinimumHeight(42)
        self._btn_export.setStyleSheet("""
            QPushButton {
                background-color: #2563EB;
                color: #FFFFFF;
                border: none;
                border-radius: 10px;
                padding: 10px 20px;
                font-size: 13px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #1D4ED8; }
        """)

        toolbar.addWidget(self._search, stretch=1)
        toolbar.addLayout(threshold_container)
        toolbar.addWidget(self._btn_refresh)
        toolbar.addWidget(self._btn_export)

        layout.addLayout(toolbar)

        # Table
        self._table = QTableWidget()
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels([
            "RANG", "COMPTEUR", "NOM", "CONSOMMATION", "VISUEL", "STATUT / ALERTE"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self._table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        self._table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self._table.setColumnWidth(0, 60)
        self._table.setColumnWidth(3, 120)
        self._table.setColumnWidth(5, 160)
        self._table.verticalHeader().setVisible(False)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.verticalHeader().setDefaultSectionSize(52)

        layout.addWidget(self._table)

        # Footer
        footer = QHBoxLayout()
        self._status = QLabel("En attente des données...")
        self._status.setStyleSheet("font-size: 12px; color: #94A3B8;")
        footer.addWidget(self._status)
        footer.addStretch()
        layout.addLayout(footer)

    def set_data(self, records):
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

            # Prevent negative data errors from backend swapping
            if cons < 0:
                cons = 0.0

            raw_prev = (
                item.get("previousConsumptionM3") or item.get("previousConsumption") or 
                item.get("previous") or item.get("ancien") or 0.0
            )
            try:
                prev = float(raw_prev)
            except (ValueError, TypeError):
                prev = 0.0

            normalized_records.append({
                "meterNumber": meter,
                "fullName": name,
                "consumptionM3": cons,
                "previousConsumptionM3": prev,
                "isPaid": bool(item.get("isPaid", item.get("paid", False)))
            })

        # CRITICAL FIX: Always sort highest consumer to lowest (Rank #1 = Highest user)
        normalized_records.sort(key=lambda x: x["consumptionM3"], reverse=True)

        self._data = normalized_records
        self._filtered = self._data[:]
        self._compute_stats()
        self._populate_table()
        self._status.setText("Données synchronisées — %d compteurs analysés" % len(self._data))

    def _compute_stats(self):
        if not self._data:
            self._kpi_total.layout().itemAt(0).widget().setText("0.0 m³")
            self._kpi_avg.layout().itemAt(0).widget().setText("0.0 m³")
            self._kpi_max.layout().itemAt(0).widget().setText("0.0 m³")
            self._kpi_active.layout().itemAt(0).widget().setText("0")
            return

        values = [r.get("consumptionM3", 0.0) for r in self._data]
        self._max_consumption = max(values) if values else 1.0
        total = sum(values)
        avg = total / len(values) if values else 0.0

        self._kpi_total.layout().itemAt(0).widget().setText("%.1f m³" % total)
        self._kpi_avg.layout().itemAt(0).widget().setText("%.1f m³" % avg)
        self._kpi_max.layout().itemAt(0).widget().setText("%.1f m³" % self._max_consumption)
        self._kpi_active.layout().itemAt(0).widget().setText("%d" % len(values))

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

    def _on_threshold_changed(self, value):
        self._populate_table()

    def _populate_table(self):
        self._table.setUpdatesEnabled(False)
        self._table.setRowCount(len(self._filtered))

        limit_m3 = self._threshold_spin.value()

        for i, record in enumerate(self._filtered):
            rank = i + 1
            meter = str(record.get("meterNumber", ""))
            name = str(record.get("fullName", ""))
            cons = float(record.get("consumptionM3", 0.0))

            # Rank Badge
            badge = RankBadge(rank, 28)
            self._table.setCellWidget(i, 0, badge)

            # Meter
            item_meter = QTableWidgetItem(meter)
            item_meter.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_meter.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            self._table.setItem(i, 1, item_meter)

            # Name
            item_name = QTableWidgetItem(name)
            item_name.setTextAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(i, 2, item_name)

            # Consumption value
            item_cons = QTableWidgetItem("%.1f m³" % cons)
            item_cons.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            item_cons.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
            self._table.setItem(i, 3, item_cons)

            # Visual bar
            bar = ConsumptionBar(cons, self._max_consumption, "#2563EB")
            bar_widget = QWidget()
            bar_layout = QVBoxLayout(bar_widget)
            bar_layout.setContentsMargins(10, 18, 10, 18)
            bar_layout.addWidget(bar)
            self._table.setCellWidget(i, 4, bar_widget)

            # Rebuilt practical operational logic for village water management
            alert_widget = QWidget()
            alert_layout = QHBoxLayout(alert_widget)
            alert_layout.setContentsMargins(6, 0, 6, 0)
            alert_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            if cons == 0.0:
                pill = AlertPill("⚫ Inactif / 0 m³", "#F1F5F9", "#475569")
            elif cons >= limit_m3:
                pill = AlertPill("🔴 Surconsommation / Fuite", "#FEE2E2", "#991B1B")
            elif cons >= (limit_m3 * 0.7):
                pill = AlertPill("🟠 Hausse notable", "#FEF3C7", "#92400E")
            else:
                pill = AlertPill("🟢 Normal", "#DCFCE7", "#166534")

            alert_layout.addWidget(pill)
            self._table.setCellWidget(i, 5, alert_widget)

            # Highlight top 3 consumers distinctly
            if rank == 1:
                item_cons.setForeground(QColor("#B45309"))
            elif rank == 2:
                item_cons.setForeground(QColor("#64748B"))
            elif rank == 3:
                item_cons.setForeground(QColor("#92400E"))

        self._table.setUpdatesEnabled(True)

    def _render_table(self):
        self._populate_table()