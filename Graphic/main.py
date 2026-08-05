# main.py
import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon

from UI.home_ui import HomeView
from UI.invoice_ui import BillingView
from UI.consomation_board_ui import ConsumptionDashboard
from UI.finance_dashboard_ui import FinanceDashboard
from workers import FetchUsersWorker


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


class MainAssociationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ASJID")
        self.setWindowIcon(QIcon(resource_path("app_icon.ico")))
        self.resize(1440, 900)
        self.setMinimumSize(QSize(1280, 800))

        self.setup_global_styles()

        # Central pipeline data store
        self.cached_records = []
        self.worker = None

        # Central Stacked Container for Multi-Page Navigation
        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        # Initialize Views
        self.home_view = HomeView()
        self.billing_view = BillingView()
        self.consomation_view = ConsumptionDashboard()
        self.finance_view = FinanceDashboard()

        # Connect navigation signals directly to page switcher
        self.home_view.navigate_signal.connect(self.switch_page)
        self.billing_view.navigate_signal.connect(self.switch_page)
        self.consomation_view.back_signal.connect(lambda: self.switch_page(0))
        self.finance_view.back_signal.connect(lambda: self.switch_page(0))
        
        # Connect refresh signals to trigger the central pipeline worker
        self.consomation_view.request_refresh_signal.connect(self.run_fetch_pipeline)
        self.finance_view.request_refresh_signal.connect(self.run_fetch_pipeline)

        # Add to Stack with exact indices matching HomeView page_index mappings
        self.stacked_widget.addWidget(self.home_view)          # Index 0: Home Page
        self.stacked_widget.addWidget(self.billing_view)       # Index 1: Billing / Invoices View
        self.stacked_widget.addWidget(self.consomation_view)   # Index 2: Consumption Dashboard
        self.stacked_widget.addWidget(self.finance_view)       # Index 3: Financial Management Dashboard

        self.stacked_widget.setCurrentIndex(0)

        # Execute master fetch pipeline immediately on launch
        self.run_fetch_pipeline()

    def run_fetch_pipeline(self):
        """Starts the worker thread to fetch data centrally from the API."""
        print("Pipeline: Starting background fetch worker...")
        if self.worker is not None and self.worker.isRunning():
            return

        self.worker = FetchUsersWorker()
        self.worker.finished.connect(self.distribute_pipeline_data)
        self.worker.start()

    def distribute_pipeline_data(self, records, error):
        """Pipeline dispatcher: receives records and broadcasts them to all views."""
        if error:
            print(f"Pipeline Error: {error}")
            return

        if records:
            self.cached_records = records

            # 1. Pipeline records to Consumption Dashboard
            self.consomation_view.set_data(records)

            # 2. Pipeline records to Financial Dashboard
            self.finance_view.set_data(records)

            # 3. Pipeline records to Billing View
            if hasattr(self.billing_view, "set_data"):
                self.billing_view.set_data(records)
            elif hasattr(self.billing_view, "load_records"):
                self.billing_view.load_records(records)
            elif hasattr(self.billing_view, "records"):
                self.billing_view.records = records
                if hasattr(self.billing_view, "populate_table"):
                    self.billing_view.populate_table()

            print(f"Pipeline Success: Broadcasted {len(records)} records to all views.")

    def switch_page(self, index):
        self.stacked_widget.setCurrentIndex(index)

    def setup_global_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F8FAFC;
            }
            QLabel {
                font-family: 'Segoe UI', -apple-system, sans-serif;
                color: #0F172A;
            }
            QPushButton.action-btn {
                background-color: #FFFFFF; 
                color: #334155;
                border: 1.5px solid #E2E8F0; 
                border-radius: 10px;
                padding: 10px 20px; 
                font-size: 14px; 
                font-weight: 600;
            }
            QPushButton.action-btn:hover { 
                background-color: #F8FAFC; 
                border-color: #CBD5E1; 
            }
            QPushButton.action-btn-active, QPushButton[active="true"] {
                background-color: #2563EB; 
                color: #FFFFFF;
                border: 1.5px solid #2563EB; 
                border-radius: 10px;
                padding: 10px 20px; 
                font-size: 14px; 
                font-weight: 700;
            }
            QPushButton.primary-btn {
                background-color: #2563EB; 
                color: #FFFFFF; 
                border: none;
                border-radius: 10px; 
                padding: 10px 22px; 
                font-size: 14px; 
                font-weight: 700;
            }
            QPushButton.primary-btn:hover { 
                background-color: #1D4ED8; 
            }
            QLineEdit {
                background-color: #FFFFFF; 
                border: 1.5px solid #E2E8F0;
                border-radius: 10px; 
                padding: 10px 14px; 
                font-size: 14px; 
                color: #0F172A;
            }
            QLineEdit:focus { 
                border: 2px solid #2563EB; 
            }
            QTableWidget {
                background-color: #FFFFFF; 
                border: 1px solid #E2E8F0;
                border-radius: 16px; 
                gridline-color: #F1F5F9; 
                font-size: 14px;
                color: #0F172A; 
                alternate-background-color: #F8FAFC; 
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
                font-size: 13px;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainAssociationApp()
    window.show()
    sys.exit(app.exec())