from PySide6.QtCore import QThread, Signal
from data import WaterApiClient


class FetchUsersWorker(QThread):
    finished = Signal(list, str)

    def __init__(self):
        super().__init__()
        self.client = WaterApiClient()

    def run(self):
        data, error = self.client.fetch_users()

        if error is not None:
            self.finished.emit([], error)
            return

        if isinstance(data, dict):
            if not data.get("success", True):
                self.finished.emit([], data.get("error", "Unknown API error"))
                return
            users_data = data.get("data", [])
        elif isinstance(data, list):
            users_data = data
        else:
            users_data = []

        self.finished.emit(users_data, "")