from PIL import Image, ImageDraw, ImageFont
import os
import sys
import json
import re
import calendar
from datetime import datetime, timezone

from settings_store import get_save_path

# Optional: install for perfect Arabic letter connections
# pip install arabic-reshaper python-bidi
try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    _ARABIC_SUPPORT = True
except ImportError:
    _ARABIC_SUPPORT = False


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class GeneratorError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Generator:
    QUEUE_FILENAME = "whatsapp_queue.json"

    # Receipt styling (matches your HTML)
    WIDTH = 320
    BG_COLOR = (243, 244, 246)       # #f3f4f6  outer background
    PAPER_COLOR = (255, 255, 255)    # #ffffff  receipt paper
    TEXT_COLOR = (17, 24, 39)        # #111827  main text
    MUTED_COLOR = (75, 85, 99)       # #4b5563  labels / small text
    DASH_COLOR = (156, 163, 175)     # #9ca3af  dashed separators
    FOOTER_MUTED = (156, 163, 175)   # #9ca3af  footer tiny text
    LIGHT_BORDER = (229, 231, 235)   # #e5e7eb  solid line above consumption

    def __init__(self, users, save_path=None):
        self.users = users
        self.path_to_save = save_path or get_save_path()
        os.makedirs(self.path_to_save, exist_ok=True)
        self._init_fonts()

    def _init_fonts(self):
        """Load Arabic-capable fonts with several fallback paths."""
        candidates = [
            resource_path(os.path.join("assets", "NotoSansArabic-Regular.ttf")),
            resource_path(os.path.join("fonts", "NotoSansArabic-Regular.ttf")),
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/tahoma.ttf",
            "/usr/share/fonts/truetype/noto/NotoSansArabic-Regular.ttf",
            "/System/Library/Fonts/GeezaPro.ttc",
        ]

        def load(size):
            for path in candidates:
                if path and os.path.exists(path):
                    try:
                        return ImageFont.truetype(path, size)
                    except Exception:
                        continue
            return ImageFont.load_default()

        self.font = load(14)        # body / rows
        self.font_bold = load(16)   # header title
        self.font_small = load(11)  # header subtitle / date
        self.font_tiny = load(9)    # footer note
        self.font_badge = load(11)  # PAID badge
        self.font_total = load(15)  # total amount

    @staticmethod
    def _normalize_phone(raw_phone):
        """Return (e164_phone, digits_only) or (None, None) if unusable.

        WhatsApp deep links (wa.me/<digits>) need digits only, no '+'.
        We keep both forms in the manifest so the extension can use
        whichever it needs without re-parsing.
        """
        if not raw_phone:
            return None, None
        cleaned = re.sub(r"[^\d+]", "", str(raw_phone).strip())
        if not cleaned:
            return None, None
        digits_only = cleaned.lstrip("+")
        if len(digits_only) < 8:  # too short to be a real phone number
            return None, None
        e164 = "+" + digits_only
        return e164, digits_only

    @staticmethod
    def _build_message(user, total_bill, consumption):
        """Default WhatsApp caption text for the invoice. Kept as its
        own method so wording can be changed in one place, or swapped
        for a Settings-configurable template later without touching
        the generation loop."""
        name = user.get("fullName", "").strip()
        meter = user.get("meterNumber", "")
        bill_date = user.get("billDate", "")
        return (
            f"Bonjour {name},\n"
            f"Voici votre facture d\'eau (compteur {meter}) pour la periode {bill_date}.\n"
            f"Consommation: {abs(consumption)} m3 - Montant: {abs(total_bill)} MAD.\n"
            f"Merci de bien vouloir regler votre facture."
        )

    def _shape_text(self, text):
        """Reshape Arabic text so letters connect properly (optional)."""
        if not _ARABIC_SUPPORT or not text:
            return text
        try:
            return get_display(arabic_reshaper.reshape(text))
        except Exception:
            return text

    def _text_size(self, draw, text, font):
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def _draw_dashed_line(self, draw, x1, y, x2, dash=4, gap=3):
        """Draw a horizontal dashed line."""
        x = x1
        while x < x2:
            draw.line([(x, y), (min(x + dash, x2), y)], fill=self.DASH_COLOR, width=1)
            x += dash + gap

    def _render_receipt(self, user):
        """Render a single invoice as a PIL Image."""
        # Temporary tall canvas for measurement
        tmp = Image.new("RGB", (self.WIDTH, 1000), self.PAPER_COLOR)
        draw = ImageDraw.Draw(tmp)

        margin = 20
        x = margin
        y = 20
        right = self.WIDTH - margin
        center = self.WIDTH // 2

        # Local aliases to avoid self. everywhere inside helpers
        TEXT_COLOR = self.TEXT_COLOR
        MUTED_COLOR = self.MUTED_COLOR
        DASH_COLOR = self.DASH_COLOR
        FOOTER_MUTED = self.FOOTER_MUTED
        LIGHT_BORDER = self.LIGHT_BORDER

        def draw_centered(text, font, color=TEXT_COLOR, dy=0):
            nonlocal y
            t = self._shape_text(text)
            w, h = self._text_size(draw, t, font)
            draw.text((center - w // 2, y), t, font=font, fill=color)
            y += h + dy

        def draw_row(label, value, font,
                     label_color=MUTED_COLOR, value_color=TEXT_COLOR, gap=6):
            nonlocal y
            l = self._shape_text(label)
            v = self._shape_text(value)
            lw, lh = self._text_size(draw, l, font)
            vw, vh = self._text_size(draw, v, font)
            h = max(lh, vh)
            # RTL layout: Arabic label on the RIGHT, value on the LEFT
            draw.text((right - lw, y), l, font=font, fill=label_color)
            draw.text((x, y), v, font=font, fill=value_color)
            y += h + gap

        # ── Header ─────────────────────────────────────────────────────
        draw_centered("وصل استهلاك الماء", self.font_bold, dy=4)
        draw_centered("جمعية شباب إدورحمان للتنمية والتعاون",
                      self.font_small, MUTED_COLOR, dy=2)

        bill_date = user.get("billDate", "")
        if not bill_date:
            now = datetime.now()
            start = now.replace(day=1).strftime("%d/%m/%Y")
            last_day = calendar.monthrange(now.year, now.month)[1]
            end = now.replace(day=last_day).strftime("%d/%m/%Y")
            bill_date = f"{end} - {start}"
        date_line = f"{bill_date} :التاريخ"
        draw_centered(date_line, self.font_small, MUTED_COLOR, dy=8)

        self._draw_dashed_line(draw, x, y, right)
        y += 14

        # ── User info ──────────────────────────────────────────────────
        meter = str(user.get("meterNumber", ""))
        name = user.get("fullName", "")
        draw_row("رقم العداد:", f"#{meter}", self.font)
        draw_row("اسم المشترك:", name, self.font)
        y += 4
        self._draw_dashed_line(draw, x, y, right)
        y += 14

        # ── Readings ───────────────────────────────────────────────────
        prev_r = str(user.get("previousReading", ""))
        curr_r = str(user.get("currentReading", ""))
        cons = str(abs(user.get("consumption", 0) or 0))
        draw_row("العداد السابق:", f"{prev_r} م³", self.font)
        draw_row("العداد الحالي:", f"{curr_r} م³", self.font)
        # Light solid line above consumption total
        draw.line([(x, y), (right, y)], fill=LIGHT_BORDER, width=1)
        y += 6
        draw_row("المستهلك:", f"{cons} م³", self.font, value_color=TEXT_COLOR)
        y += 4
        self._draw_dashed_line(draw, x, y, right)
        y += 14

        # ── Total ──────────────────────────────────────────────────────
        total = str(abs(user.get("totalBill", 0) or 0))
        draw_row("المبلغ الإجمالي:", f"{total} درهم", self.font_total,
                 label_color=TEXT_COLOR, value_color=TEXT_COLOR, gap=10)
        self._draw_dashed_line(draw, x, y, right)
        y += 14

        # ── Footer ─────────────────────────────────────────────────────
        badge_text = "تم الدفع / PAID"
        bt = self._shape_text(badge_text)
        bw, bh = self._text_size(draw, bt, self.font_badge)
        badge_w, badge_h = bw + 20, bh + 8
        badge_x = center - badge_w // 2
        draw.rectangle(
            [badge_x, y, badge_x + badge_w, y + badge_h],
            outline=TEXT_COLOR, width=1
        )
        draw.text((center - bw // 2, y + 4), bt,
                  font=self.font_badge, fill=TEXT_COLOR)
        y += badge_h + 8

        thanks = "شكراً لتسوية مستحقاتكم في الوقت المحدد"
        tt = self._shape_text(thanks)
        tw, th = self._text_size(draw, tt, self.font_tiny)
        draw.text((center - tw // 2, y), tt,
                  font=self.font_tiny, fill=FOOTER_MUTED)
        y += th + 20

        # ── Crop to content & add grey background padding ─────────────
        receipt_h = y
        receipt = tmp.crop((0, 0, self.WIDTH, receipt_h))

        padding = 20
        final = Image.new("RGB",
                          (self.WIDTH + padding * 2, receipt_h + padding * 2),
                          self.BG_COLOR)
        final.paste(receipt, (padding, padding))
        return final

    def generate_bills(self):
        queue = []
        skipped = []

        for user in self.users:
            # Guard: users passed in should be dicts (raw API records),
            # not display tuples. Fail loudly and clearly if that
            # contract is ever broken again upstream.
            if not isinstance(user, dict):
                raise GeneratorError(
                    f"Expected a dict record, got {type(user).__name__}: {user!r}"
                )

            meter = user.get("meterNumber")
            # None-safe: abs(None) raises TypeError and previously
            # crashed the whole batch on any record missing these
            # fields. Default to 0 instead, so one bad row doesn't
            # take down the entire invoice run.
            consumption = user.get("consumption", 0) or 0
            total_bill = user.get("totalBill", 0) or 0

            img = self._render_receipt(user)
            filename = f"{meter}.png"
            filepath = os.path.join(self.path_to_save, filename)
            img.save(filepath, "PNG")
            print(f"DEBUG: Successfully generated -> {filename}")

            e164_phone, digits_only = self._normalize_phone(user.get("phone"))
            entry = {
                "meterNumber": str(meter),
                "fullName": user.get("fullName", ""),
                "phone": e164_phone,
                "whatsappNumber": digits_only,  # digits only, for wa.me/<number>
                "invoiceFile": filename,
                "invoicePath": filepath,
                "amount": abs(total_bill),
                "consumption": abs(consumption),
                "billDate": user.get("billDate", ""),
                "message": self._build_message(user, total_bill, consumption),
                "sent": False,
                "sentAt": None,
            }

            if e164_phone:
                queue.append(entry)
            else:
                entry["skipReason"] = "missing_or_invalid_phone_number"
                skipped.append(entry)

        self._write_queue_manifest(queue, skipped)

    def _write_queue_manifest(self, queue, skipped):
        """Writes whatsapp_queue.json alongside the generated images."""
        manifest = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "saveFolder": self.path_to_save,
            "totalGenerated": len(queue) + len(skipped),
            "readyToSend": len(queue),
            "skippedNoPhone": len(skipped),
            "queue": queue,
            "skipped": skipped,
        }
        manifest_path = os.path.join(self.path_to_save, self.QUEUE_FILENAME)
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print(f"DEBUG: WhatsApp queue manifest written -> {manifest_path}")