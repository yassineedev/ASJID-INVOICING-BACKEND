"""
Centralized, persistent app settings using QSettings.

QSettings stores these in the OS-native location on Windows
(registry, under HKEY_CURRENT_USER\\Software\\<ORG>\\<APP>), so no
extra config file to manage or lose on redeploy.
"""

from PySide6.QtCore import QSettings

ORG_NAME = "WaterAssociation"
APP_NAME = "BillsGenerator"

# Fall back to today's hardcoded values so existing behavior doesn't
# change until someone actually opens Settings and edits them.
DEFAULT_API_URL = (
    "https://script.google.com/macros/s/"
    "AKfycbzR4ayLk5HUYAFpilIWUm7ay9ga_5IcwwtOyUc50_MC9hkt5ueYeHyz_HniFGXo5Hs/exec"
)
DEFAULT_SAVE_PATH = "/home/enissay/project/bills-generator/Graphic/generated"

KEY_API_URL = "api/url"
KEY_SAVE_PATH = "invoices/save_path"


def _settings() -> QSettings:
    return QSettings(ORG_NAME, APP_NAME)


def get_api_url() -> str:
    return _settings().value(KEY_API_URL, DEFAULT_API_URL, type=str)


def set_api_url(url: str) -> None:
    _settings().setValue(KEY_API_URL, url.strip())


def get_save_path() -> str:
    return _settings().value(KEY_SAVE_PATH, DEFAULT_SAVE_PATH, type=str)


def set_save_path(path: str) -> None:
    _settings().setValue(KEY_SAVE_PATH, path.strip())