from PyQt6.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt
from ui.client_window_ui import Ui_ClientsWindow
from session import Session
from db import Database

class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ClientsWindow()
        self.ui.setupUi(self)

        self.user = Session.get_user()
        if not self.user:
            self.close()
            return

        self.setWindowTitle(f"Личный кабинет клиента - СПбЦ ЭЛМА | {self.user.get('display_name', 'Клиент')}")

        self._setup_navigation()
        self._setup_tables()
        self._load_all_data()

    def _setup_navigation(self):
        self.ui.btnHome.clicked.connect(lambda: self._show_page(self.ui.pageHome, self.ui.btnHome))
        self.ui.btnMyOrders.clicked.connect(lambda: self._show_page(self.ui.pageMyOrders, self.ui.btnMyOrders))
        self.ui.btnResults.clicked.connect(lambda: self._show_page(self.ui.pageResults, self.ui.btnResults))
        self.ui.btnDocuments.clicked.connect(lambda: self._show_page(self.ui.pageDocuments, self.ui.btnDocuments))
        self.ui.btnProfile.clicked.connect(lambda: self._show_page(self.ui.pageProfile, self.ui.btnProfile))
        self.ui.btnLogout.clicked.connect(self._logout)
        self._show_page(self.ui.pageHome, self.ui.btnHome)

    def _show_page(self, page, active_btn):
        self.ui.clientStackedWidget.setCurrentWidget(page)
        for btn in [self.ui.btnHome, self.ui.btnMyOrders, self.ui.btnResults, self.ui.btnDocuments, self.ui.btnProfile]:
            btn.setChecked(False)
        active_btn.setChecked(True)

    def _setup_tables(self):
        for table in [self.ui.tableHomeOrders, self.ui.tableMyOrders, self.ui.tableResults, self.ui.tableDocuments]:
            table.setWordWrap(True)
            table.setTextElideMode(Qt.TextElideMode.ElideNone)
            table.verticalHeader().setVisible(False)
            table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

    def _load_all_data(self):
        self._load_home_stats()
        self._load_home_orders()
        self._load_my_orders()
        self._load_results()
        self._load_documents()
        self._load_profile()

    def _load_home_stats(self):
        stats = Database().get_client_stats(Session.get_user_id())
        if stats:
            self.ui.statValue.setText(str(stats.get('total_orders', 0)))
            self.ui.statValue1.setText(str(stats.get('active_orders', 0)))
            self.ui.statValue2.setText(str(stats.get('completed_orders', 0)))

    def _load_home_orders(self):
        orders = Database().get_client_orders(Session.get_user_id(), limit=5)
        self.ui.tableHomeOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            self.ui.tableHomeOrders.setItem(row_idx, 0, QTableWidgetItem(str(order.get('vessel_code', ''))))
            self.ui.tableHomeOrders.setItem(row_idx, 1, QTableWidgetItem(str(order.get('order_date', ''))))
            self.ui.tableHomeOrders.setItem(row_idx, 2, QTableWidgetItem(str(order.get('services_count', 0))))
            item = QTableWidgetItem(str(order.get('status', '')))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableHomeOrders.setItem(row_idx, 3, item)

    def _load_my_orders(self):
        orders = Database().get_client_orders(Session.get_user_id())
        self.ui.tableMyOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            self.ui.tableMyOrders.setItem(row_idx, 0, QTableWidgetItem(str(order.get('vessel_code', ''))))
            self.ui.tableMyOrders.setItem(row_idx, 1, QTableWidgetItem(str(order.get('order_date', ''))))
            self.ui.tableMyOrders.setItem(row_idx, 2, QTableWidgetItem(str(order.get('vessel_code', ''))))
            self.ui.tableMyOrders.setItem(row_idx, 3, QTableWidgetItem(str(order.get('services_list', ''))))
            self.ui.tableMyOrders.setItem(row_idx, 4, QTableWidgetItem(str(order.get('total_price', 0))))
            item = QTableWidgetItem(str(order.get('status', '')))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableMyOrders.setItem(row_idx, 5, item)

    def _load_results(self):
        results = Database().get_client_results(Session.get_user_id())
        self.ui.tableResults.setRowCount(len(results))
        for row_idx, res in enumerate(results):
            self.ui.tableResults.setItem(row_idx, 0, QTableWidgetItem(str(res.get('vessel_code', ''))))
            self.ui.tableResults.setItem(row_idx, 1, QTableWidgetItem(str(res.get('service_name', ''))))
            self.ui.tableResults.setItem(row_idx, 2, QTableWidgetItem(str(res.get('result_date', ''))))
            self.ui.tableResults.setItem(row_idx, 3, QTableWidgetItem(str(res.get('result_value', ''))))
            self.ui.tableResults.setItem(row_idx, 4, QTableWidgetItem(str(res.get('conclusion', ''))))
            self.ui.tableResults.setItem(row_idx, 5, QTableWidgetItem(str(res.get('employee_name', ''))))

    def _load_documents(self):
        reports = Database().get_client_reports(Session.get_user_id())
        self.ui.tableDocuments.setRowCount(len(reports))
        for row_idx, rep in enumerate(reports):
            self.ui.tableDocuments.setItem(row_idx, 0, QTableWidgetItem(f"ОТЧ-{rep.get('report_id', 0):04d}"))
            self.ui.tableDocuments.setItem(row_idx, 1, QTableWidgetItem("Отчёт"))
            self.ui.tableDocuments.setItem(row_idx, 2, QTableWidgetItem(str(rep.get('vessel_code', ''))))
            self.ui.tableDocuments.setItem(row_idx, 3, QTableWidgetItem(str(rep.get('report_date', ''))))

    def _load_profile(self):
        info = Database().get_client_info(Session.get_user_id())
        if info:
            self.ui.lblProfileName.setText(info.get('name', 'Не указано'))
            self.ui.lblProfileContact.setText(info.get('contact_person', 'Не указано'))
            self.ui.lblProfilePhone.setText(info.get('phone', 'Не указан'))
            self.ui.lblProfileEmail.setText(info.get('email', 'Не указана'))

    def _logout(self):
        if QMessageBox.question(self, "Выход", "Выйти из личного кабинета?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            Session.clear()
            self.close()