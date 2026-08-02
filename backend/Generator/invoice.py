from html2image import Html2Image
from PIL import Image
import os


class GeneratorError(Exception):
    def __init__(self, msg):
        super().__init__(msg)


class Generator:
    def __init__(self, users):
        self.users = users
        self.p = "/home/enissay/project/bills-generator/backend/template/v.html"
        self.path_to_save = (
            "/home/enissay/project/bills-generator/backend/Generator/images"
        )
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
        try:
            with open(self.p, "r", encoding="UTF-8") as tp:
                html = tp.read()
            for user in self.users:
                meter = user.get("meterNumber")
                content = html.format(
                    meterNumber=meter,
                    fullName=user.get("fullName"),
                    previousReading=user.get("previousReading"),
                    currentReading=user.get("currentReading"),
                    consumption=abs(user.get("consumption")),
                    totalBill=abs(user.get("totalBill")),
                )
                filename = f"{meter}.png"
                self.h.screenshot(
                    html_str=content,
                    save_as=filename,
                    size=(500, 700),
                )
                self._crop_to_content(os.path.join(self.path_to_save, filename))
                print(f"DEBUG: Successfully generated -> {filename}")
        except FileNotFoundError as e:
            print(f"Detailed Error: {e}")
            raise GeneratorError(e)
