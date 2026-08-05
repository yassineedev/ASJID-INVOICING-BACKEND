# UI/home_ui.py
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QGraphicsDropShadowEffect, QFrame, QSizePolicy, QGraphicsOpacityEffect,
)
from PySide6.QtCore import (
    Qt, Signal, QPropertyAnimation, QEasingCurve,
    QPointF, QTimer,
)
from PySide6.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen, QLinearGradient, QRadialGradient,
    QCursor, QPainterPath,
)


class AmbientBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()

        base = QLinearGradient(0, 0, w, h)
        base.setColorAt(0.0, QColor("#F8FAFC"))
        base.setColorAt(0.5, QColor("#F1F5F9"))
        base.setColorAt(1.0, QColor("#EEF2F6"))
        painter.fillRect(self.rect(), QBrush(base))

        orb1 = QRadialGradient(w * 0.75, h * 0.25, w * 0.45)
        orb1.setColorAt(0.0, QColor(37, 99, 235, 18))
        orb1.setColorAt(0.5, QColor(37, 99, 235, 6))
        orb1.setColorAt(1.0, QColor(37, 99, 235, 0))
        painter.setBrush(QBrush(orb1))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(int(w * 0.3), int(-h * 0.1), int(w * 0.9), int(h * 0.7))

        orb2 = QRadialGradient(w * 0.2, h * 0.8, w * 0.4)
        orb2.setColorAt(0.0, QColor(124, 58, 237, 14))
        orb2.setColorAt(0.5, QColor(124, 58, 237, 5))
        orb2.setColorAt(1.0, QColor(124, 58, 237, 0))
        painter.setBrush(QBrush(orb2))
        painter.drawEllipse(int(-w * 0.15), int(h * 0.45), int(w * 0.7), int(h * 0.6))


class IconBadge(QWidget):
    def __init__(self, icon_type, size=80, parent=None):
        super().__init__(parent)
        self.icon_type = icon_type
        self.setFixedSize(size, size)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        s = self.width()
        r = s // 2
        center = self.rect().center()

        if self.icon_type == "invoice":
            grad = QLinearGradient(0, 0, s, s)
            grad.setColorAt(0.0, QColor("#3B82F6"))
            grad.setColorAt(1.0, QColor("#2563EB"))
        elif self.icon_type == "analytics":
            grad = QLinearGradient(0, 0, s, s)
            grad.setColorAt(0.0, QColor("#10B981"))
            grad.setColorAt(1.0, QColor("#059669"))
        else:  # finance
            grad = QLinearGradient(0, 0, s, s)
            grad.setColorAt(0.0, QColor("#8B5CF6"))
            grad.setColorAt(1.0, QColor("#7C3AED"))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(self.rect().adjusted(2, 2, -2, -2))

        inner = QRadialGradient(center, r * 0.85)
        inner.setColorAt(0.0, QColor(255, 255, 255, 30))
        inner.setColorAt(1.0, QColor(255, 255, 255, 0))
        painter.setBrush(QBrush(inner))
        painter.drawEllipse(self.rect().adjusted(4, 4, -4, -4))

        painter.setPen(QPen(QColor("#FFFFFF")))
        painter.setBrush(QBrush(QColor("#FFFFFF")))

        if self.icon_type == "invoice":
            self._draw_invoice(painter, s)
        elif self.icon_type == "analytics":
            self._draw_analytics(painter, s)
        else:
            self._draw_finance(painter, s)

    def _draw_invoice(self, p, s):
        doc_w, doc_h = s * 0.44, s * 0.50
        x, y = (s - doc_w) / 2, (s - doc_h) / 2
        p.setPen(QPen(QColor("#FFFFFF"), 2.5))
        p.setBrush(Qt.BrushStyle.NoBrush)
        path = QPainterPath()
        path.moveTo(x, y + 6)
        path.lineTo(x, y + doc_h - 6)
        path.arcTo(x, y + doc_h - 12, 12, 12, 180, 90)
        path.lineTo(x + doc_w - 6, y + doc_h)
        path.arcTo(x + doc_w - 12, y + doc_h - 12, 12, 12, 270, 90)
        path.lineTo(x + doc_w, y + 6)
        path.arcTo(x + doc_w - 12, y, 12, 12, 0, 90)
        path.lineTo(x + 6, y)
        path.arcTo(x, y, 12, 12, 90, 90)
        p.drawPath(path)
        p.drawLine(int(x + doc_w - 14), int(y), int(x + doc_w), int(y + 14))

    def _draw_analytics(self, p, s):
        bar_w = s * 0.10
        gap = s * 0.06
        base_y = s * 0.72
        x_start = s * 0.25
        heights = [s * 0.18, s * 0.32, s * 0.24]
        for i, h in enumerate(heights):
            x = x_start + i * (bar_w + gap)
            y = base_y - h
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(QColor("#FFFFFF")))
            p.drawRoundedRect(int(x), int(y), int(bar_w), int(h + 4), 3, 3)

    def _draw_finance(self, p, s):
        w_rect, h_rect = s * 0.52, s * 0.36
        x, y = (s - w_rect) / 2, (s - h_rect) / 2
        p.setPen(QPen(QColor("#FFFFFF"), 2.2))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(int(x), int(y), int(w_rect), int(h_rect), 6, 6)
        p.setBrush(QBrush(QColor("#FFFFFF")))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRect(int(x), int(y + h_rect * 0.25), int(w_rect), int(h_rect * 0.2))
        p.drawRoundedRect(int(x + w_rect * 0.15), int(y + h_rect * 0.6), int(w_rect * 0.2), int(h_rect * 0.22), 3, 3)


class ModuleCard(QFrame):
    """Premium interactive card using native QSS hover states (100% crash-free)."""

    def __init__(self, icon_type, accent_color, hover_color, title, description,
                 action_text, page_index, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.accent_color = accent_color
        self.hover_color = hover_color

        self.setFixedSize(320, 400)
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        self._shadow = QGraphicsDropShadowEffect(self)
        self._shadow.setBlurRadius(28)
        self._shadow.setColor(QColor(0, 0, 0, 18))
        self._shadow.setOffset(QPointF(0, 8))
        self.setGraphicsEffect(self._shadow)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(32, 36, 32, 32)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self._icon = IconBadge(icon_type, 80, self)
        self._layout.addWidget(self._icon, alignment=Qt.AlignmentFlag.AlignLeft)
        self._layout.addSpacing(28)

        self._title = QLabel(title)
        self._title.setStyleSheet("font-size: 22px; font-weight: 700; color: #0F172A;")
        self._layout.addWidget(self._title)
        self._layout.addSpacing(10)

        self._desc = QLabel(description)
        self._desc.setWordWrap(True)
        self._desc.setStyleSheet("font-size: 14px; color: #64748B; line-height: 1.6;")
        self._layout.addWidget(self._desc)
        self._layout.addStretch()

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self._arrow = QLabel("→")
        self._arrow.setStyleSheet("font-size: 16px; color: %s; font-weight: 700;" % accent_color)
        self._action = QLabel(action_text)
        self._action.setStyleSheet("font-size: 14px; font-weight: 600; color: %s;" % accent_color)
        action_row.addWidget(self._arrow)
        action_row.addWidget(self._action)
        action_row.addStretch()
        self._layout.addLayout(action_row)

        self.setStyleSheet("""
            ModuleCard {
                background-color: #FFFFFF;
                border-radius: 24px;
                border: 1px solid #E2E8F0;
            }
            ModuleCard:hover {
                background-color: #FFFFFF;
                border-radius: 24px;
                border: 1.5px solid %s;
            }
        """ % accent_color)

    def mouseReleaseEvent(self, event):
        home = self.parent()
        while home and not isinstance(home, HomeView):
            home = home.parent()
        if home:
            home.navigate_signal.emit(self.page_index)
        super().mouseReleaseEvent(event)


class HomeView(QWidget):
    navigate_signal = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._anims = []
        self._build_ui()
        self._animate_entrance()

    def _build_ui(self):
        self._bg = AmbientBackground(self)
        self._bg.setGeometry(self.rect())

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        header = QVBoxLayout()
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setSpacing(10)

        brand_row = QHBoxLayout()
        brand_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        brand_row.setSpacing(12)

        dot = QLabel("●")
        dot.setStyleSheet("font-size: 10px; color: #3B82F6;")
        brand_text = QLabel("ASJID")
        brand_text.setStyleSheet("font-size: 13px; font-weight: 700; color: #3B82F6; letter-spacing: 3px;")
        brand_row.addWidget(dot)
        brand_row.addWidget(brand_text)

        self._title = QLabel("Association de la Jeunesse d'Idourhamane")
        self._title.setStyleSheet("font-size: 32px; font-weight: 800; color: #0F172A;")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._subtitle = QLabel("pour le Développement et la Coopération")
        self._subtitle.setStyleSheet("font-size: 17px; font-weight: 500; color: #64748B;")
        self._subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        divider = QFrame()
        divider.setFixedSize(48, 3)
        divider.setStyleSheet("QFrame { background-color: #3B82F6; border-radius: 2px; }")

        header.addLayout(brand_row)
        header.addSpacing(16)
        header.addWidget(self._title)
        header.addWidget(self._subtitle)
        header.addSpacing(16)
        header.addWidget(divider, alignment=Qt.AlignmentFlag.AlignCenter)

        cards_row = QHBoxLayout()
        cards_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cards_row.setSpacing(24)

        self._card_invoice = ModuleCard(
            icon_type="invoice",
            accent_color="#2563EB",
            hover_color="#1D4ED8",
            title="Générer Factures",
            description="Créez des factures PDF professionnelles et préparez la file d'attente WhatsApp.",
            action_text="Ouvrir le module",
            page_index=1,
            parent=self,
        )

        self._card_analytics = ModuleCard(
            icon_type="analytics",
            accent_color="#059669",
            hover_color="#047857",
            title="Analyse Consommation",
            description="Surveillez l'utilisation de l'eau, détectez les anomalies et identifiez les fuites.",
            action_text="Ouvrir le tableau de bord",
            page_index=2,
            parent=self,
        )

        self._card_finance = ModuleCard(
            icon_type="finance",
            accent_color="#7C3AED",
            hover_color="#6D28D9",
            title="Gestion Financière",
            description="Suivez les entrées prévues, les paiements encaissés et le bilan de recouvrement.",
            action_text="Ouvrir le module",
            page_index=3,
            parent=self,
        )

        cards_row.addWidget(self._card_invoice)
        cards_row.addWidget(self._card_analytics)
        cards_row.addWidget(self._card_finance)

        footer = QVBoxLayout()
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setSpacing(6)

        footer_line = QFrame()
        footer_line.setFixedSize(120, 1)
        footer_line.setStyleSheet("background-color: #E2E8F0;")
        footer_title = QLabel("ASJID Desktop Suite")
        footer_title.setStyleSheet("font-size: 12px; font-weight: 600; color: #94A3B8; letter-spacing: 1px;")
        footer_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        footer.addWidget(footer_line, alignment=Qt.AlignmentFlag.AlignCenter)
        footer.addWidget(footer_title)

        main_layout.addStretch(3)
        main_layout.addLayout(header)
        main_layout.addSpacing(48)
        main_layout.addLayout(cards_row)
        main_layout.addStretch(2)
        main_layout.addLayout(footer)
        main_layout.addSpacing(28)

    def resizeEvent(self, event):
        self._bg.setGeometry(self.rect())
        super().resizeEvent(event)

    def _animate_entrance(self):
        widgets = [self._title, self._subtitle, self._card_invoice, self._card_analytics, self._card_finance]
        for w in widgets:
            eff = QGraphicsOpacityEffect(w)
            w.setGraphicsEffect(eff)
            eff.setOpacity(0.0)

        def make_fade(widget, delay):
            eff = widget.graphicsEffect()
            anim = QPropertyAnimation(eff, b"opacity", self)
            anim.setDuration(600)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            self._anims.append(anim)
            QTimer.singleShot(delay, anim.start)

        make_fade(self._title, 100)
        make_fade(self._subtitle, 200)
        make_fade(self._card_invoice, 350)
        make_fade(self._card_analytics, 500)
        make_fade(self._card_finance, 650)