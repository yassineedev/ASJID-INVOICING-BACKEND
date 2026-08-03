from html2image import Html2Image
from PIL import Image
import os
import json
import re
from datetime import datetime, timezone

from settings_store import get_save_path


class GeneratorError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Generator:
    QUEUE_FILENAME = "whatsapp_queue.json"

    def __init__(self, users, save_path=None):
        self.users = users
        self.p = "/home/enissay/project/bills-generator/Graphic/template/v.html"
        # Use the path configured in Settings unless the caller
        # explicitly overrides it (e.g. for tests).
        self.path_to_save = save_path or get_save_path()
        os.makedirs(self.path_to_save, exist_ok=True)
        self.h: Html2Image = Html2Image(
            output_path=self.path_to_save,
            custom_flags=[
                "--no-sandbox",
                "--disable-gpu",
                "--disable-dev-shm-usage",
                "--disable-software-rasterizer",
                "--hide-scrollbars",
            ],
        )

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
            f"Voici votre facture d'eau (compteur {meter}) pour la periode {bill_date}.\n"
            f"Consommation: {abs(consumption)} m3 - Montant: {abs(total_bill)} MAD.\n"
            f"Merci de bien vouloir regler votre facture."
        )

    def _crop_to_content(self, path, bg_color=(243, 244, 246)):
        """Trim uniform background border around the receipt."""
        img = Image.open(path).convert("RGB")
        bg = Image.new("RGB", img.size, bg_color)
        diff = Image.frombytes(
            "L",
            img.size,
            bytes(
                0 if p1 == p2 else 255 for p1, p2 in zip(img.getdata(), bg.getdata())
            ),
        )
        bbox = diff.getbbox()
        if bbox:
            img.crop(bbox).save(path)

    def generate_bills(self):
        queue = []
        skipped = []

        try:
            with open(self.p, "r", encoding="UTF-8") as tp:
                html = tp.read()

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

                content = html.format(
                    meterNumber=meter,
                    fullName=user.get("fullName"),
                    previousReading=user.get("previousReading"),
                    currentReading=user.get("currentReading"),
                    consumption=abs(consumption),
                    totalBill=abs(total_bill),
                )
                filename = f"{meter}.png"
                self.h.screenshot(
                    html_str=content,
                    save_as=filename,
                    size=(500, 700),
                )
                self._crop_to_content(os.path.join(self.path_to_save, filename))
                print(f"DEBUG: Successfully generated -> {filename}")

                e164_phone, digits_only = self._normalize_phone(user.get("phone"))
                entry = {
                    "meterNumber": str(meter),
                    "fullName": user.get("fullName", ""),
                    "phone": e164_phone,
                    "whatsappNumber": digits_only,  # digits only, for wa.me/<number>
                    "invoiceFile": filename,
                    "invoicePath": os.path.join(self.path_to_save, filename),
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

        except FileNotFoundError as e:
            print(f"Detailed Error: {e}")
            raise GeneratorError(e)

    def _write_queue_manifest(self, queue, skipped):
        """Writes whatsapp_queue.json alongside the generated images.

        The Chrome extension is expected to:
          1. Load this file (e.g. via a file input, or a small local
             server pointed at the save folder).
          2. Iterate `queue` in order, find each contact on WhatsApp
             Web using `phone` / `whatsappNumber`, attach `invoiceFile`
             from the same folder, send `message`, then move to the
             next entry - looping until the array is exhausted.
          3. Entries in `skipped` have no usable phone number and
             should be surfaced to the user rather than silently
             dropped, since those invoices still need to be delivered
             some other way (in person, SMS, etc.).
        """
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