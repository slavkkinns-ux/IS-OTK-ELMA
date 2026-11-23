from PyQt6.QtWidgets import QMainWindow, QHeaderView, QMessageBox, QTableWidgetItem
from PyQt6.QtCore import Qt

from db.client_repo import get_client_by_id
from ui.client_window_ui import Ui_ClientsWindow
from session import Session
from db import client_repo
import os
import sys

class ClientWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ClientsWindow()
        self.ui.setupUi(self)

        self._apply_style()  # Применяем единый стиль как в main_window

        self.user = Session.get_user()
        if not self.user:
            self.close()
            return

        self.setWindowTitle(f"Личный кабинет клиента - СПбЦ ЭЛМА | {self.user.get('display_name', 'Клиент')}")

        self._setup_navigation()
        self._setup_tables()
        self._load_all_data()

    def _apply_style(self):
        """Применяет единый стиль окна, аналогичный main_window."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #F4F7FB;
            }
            QFrame#sidebarFrame {
                background-color: #2c3e50;
                border: none;
            }
            QFrame#contentFrame {
                background-color: #F4F7FB;
                border: none;
            }
            QFrame#cardFrame, QFrame#statsCard, QFrame#statsCard2, QFrame#statsCard3,
            QFrame#notificationsFrame, QFrame#profileCard {
                background-color: #FFFFFF;
                border: 1px solid #DCE5EF;
                border-radius: 12px;
            }
            QLabel {
                color: #24364B;
            }
            QLabel#logoLabel {
                color: #FFFFFF;
                font-size: 20pt;
                font-weight: bold;
            }
            QLabel#sidebarSubtitle {
                color: #DCE6F1;
                font-size: 8pt;
                padding: 8px;
            }
            QLabel#pageTitle, QLabel#pageTitle1, QLabel#pageTitle2, QLabel#pageTitle3, QLabel#pageTitle4 {
                font-size: 24px;
                font-weight: bold;
                color: #17365D;
            }
            QLabel#pageSubtitle, QLabel#pageSubtitle1, QLabel#pageSubtitle2, QLabel#pageSubtitle3, QLabel#pageSubtitle4 {
                color: #60758E;
                font-size: 13px;
            }
            QLabel#statValue, QLabel#statValue1, QLabel#statValue2 {
                color: #17365D;
                font-size: 26px;
                font-weight: bold;
            }
            QLabel#statCaption, QLabel#statCaption1, QLabel#statCaption2 {
                color: #60758E;
                font-size: 13px;
            }
            QLabel#sectionTitle, QLabel#sectionTitle1 {
                font-size: 16px;
                font-weight: bold;
                color: #17365D;
            }
            QLabel#lblProfileNameTitle, QLabel#lblProfileContactTitle,
            QLabel#lblProfilePhoneTitle, QLabel#lblProfileEmailTitle {
                font-weight: bold;
                color: #24364B;
            }
            QLabel#lblProfileName, QLabel#lblProfileContact,
            QLabel#lblProfilePhone, QLabel#lblProfileEmail {
                color: #24364B;
            }
            QPushButton {
                color: #FFFFFF;
                background-color: #2b82d9;
                border: none;
                border-radius: 7px;
                text-align: left;
                padding: 10px 14px;
                font-size: 10pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #245A91;
            }
            QPushButton:checked {
                background-color: #102A49;
            }
            QPushButton#btnLogout:hover {
                background-color: #5c000f;
            }
            QPushButton#btnPrimary {
                background-color: #2D83D5;
                color: white;
                text-align: center;
                padding: 10px 18px;
            }
            QPushButton#btnPrimary:hover {
                background-color: #246EBA;
            }
            QLineEdit, QComboBox {
                background: white;
                border: 1px solid #DCE5EF;
                border-radius: 6px;
                padding: 8px;
                min-height: 22px;
            }
            QTableWidget {
                background: white;
                border: 1px solid #DCE5EF;
                border-radius: 7px;
                gridline-color: #E8EDF3;
                selection-background-color: #DCEBFA;
                selection-color: #183B63;
            }
            QHeaderView::section {
                background: #EDF2F7;
                color: #183B63;
                padding: 9px;
                border: none;
                font-weight: bold;
            }
        """)
        # Убираем инлайн-стили, заданные в UI файле
        self.ui.statsCard2.setStyleSheet("")
        self.ui.statsCard3.setStyleSheet("")
        self.ui.notificationsFrame.setStyleSheet("")
        self.ui.profileCard.setStyleSheet("")

    def _setup_navigation(self):
        self.ui.btnHome.clicked.connect(lambda: self._show_page(self.ui.pageHome, self.ui.btnHome))
        self.ui.btnMyOrders.clicked.connect(lambda: self._show_page(self.ui.pageMyOrders, self.ui.btnMyOrders))
        self.ui.btnResults.clicked.connect(lambda: self._show_page(self.ui.pageResults, self.ui.btnResults))
        self.ui.btnDocuments.clicked.connect(lambda: self._show_page(self.ui.pageDocuments, self.ui.btnDocuments))
        self.ui.btnProfile.clicked.connect(lambda: self._show_page(self.ui.pageProfile, self.ui.btnProfile))
        self.ui.btnLogout.clicked.connect(self._logout)
        self.ui.btnPrimary.clicked.connect(self._open_document)
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
        stats = client_repo.get_client_stats(Session.get_user_id())
        if stats:
            self.ui.statValue.setText(str(stats.get('total_orders', 0)))
            self.ui.statValue1.setText(str(stats.get('active_orders', 0)))
            self.ui.statValue2.setText(str(stats.get('completed_orders', 0)))

    def _load_home_orders(self):
        orders = client_repo.get_client_orders(Session.get_user_id(), limit=5)
        self.ui.tableHomeOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            self.ui.tableHomeOrders.setItem(row_idx, 0, QTableWidgetItem(str(order.get('vessel_code', ''))))
            self.ui.tableHomeOrders.setItem(row_idx, 1, QTableWidgetItem(str(order.get('order_date', ''))))
            self.ui.tableHomeOrders.setItem(row_idx, 2, QTableWidgetItem(str(order.get('services_count', 0))))
            item = QTableWidgetItem(str(order.get('status', '')))
            item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableHomeOrders.setItem(row_idx, 3, item)

    def _load_my_orders(self):
        orders = client_repo.get_client_orders(Session.get_user_id())
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
        results = client_repo.get_client_results(Session.get_user_id())
        self.ui.tableResults.setRowCount(len(results))
        for row_idx, res in enumerate(results):
            self.ui.tableResults.setItem(row_idx, 0, QTableWidgetItem(str(res.get('vessel_code', ''))))
            self.ui.tableResults.setItem(row_idx, 1, QTableWidgetItem(str(res.get('service_name', ''))))
            self.ui.tableResults.setItem(row_idx, 2, QTableWidgetItem(str(res.get('result_date', ''))))
            self.ui.tableResults.setItem(row_idx, 3, QTableWidgetItem(str(res.get('result_value', ''))))
            self.ui.tableResults.setItem(row_idx, 4, QTableWidgetItem(str(res.get('conclusion', ''))))
            self.ui.tableResults.setItem(row_idx, 5, QTableWidgetItem(str(res.get('employee_name', ''))))

    def _load_documents(self):
        reports = client_repo.get_client_reports(Session.get_user_id())
        # Фильтруем только отчёты, у которых есть файл на диске
        valid_reports = []
        for rep in reports:
            file_path = rep.get('file_path', '')
            if file_path and os.path.exists(file_path):
                valid_reports.append(rep)
        
        self.ui.tableDocuments.setRowCount(len(valid_reports))
        for row_idx, rep in enumerate(valid_reports):
            report_id = rep.get('report_id', 0)
            file_path = rep.get('file_path', '')
            
            item_doc = QTableWidgetItem(f"ОТЧ-{report_id:04d}")
            item_doc.setData(Qt.ItemDataRole.UserRole, file_path)
            self.ui.tableDocuments.setItem(row_idx, 0, item_doc)
            
            self.ui.tableDocuments.setItem(row_idx, 1, QTableWidgetItem("Отчёт"))
            self.ui.tableDocuments.setItem(row_idx, 2, QTableWidgetItem(str(rep.get('vessel_code', ''))))
            self.ui.tableDocuments.setItem(row_idx, 3, QTableWidgetItem(str(rep.get('report_date', ''))))

    def _load_profile(self):
        info = client_repo.get_client_info(Session.get_user_id())
        if info:
            self.ui.lblProfileName.setText(info.get('name', 'Не указано'))
            self.ui.lblProfileContact.setText(info.get('contact_person', 'Не указано'))
            self.ui.lblProfilePhone.setText(info.get('phone', 'Не указан'))
            self.ui.lblProfileEmail.setText(info.get('email', 'Не указана'))

    def _open_document(self):
        """Открыть выбранный документ (PDF отчёт)."""
        row = self.ui.tableDocuments.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Открытие документа", "Выберите документ в таблице.")
            return

        item = self.ui.tableDocuments.item(row, 0)
        if not item:
            QMessageBox.warning(self, "Открытие документа", "Не удалось получить данные документа.")
            return

        file_path = item.data(Qt.ItemDataRole.UserRole)
        if not file_path or not os.path.exists(file_path):
            QMessageBox.warning(self, "Открытие документа", 
                                "Файл документа не найден на диске.")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(file_path)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', file_path])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', file_path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def _logout(self):
        if QMessageBox.question(self, "Выход", "Выйти из личного кабинета?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            Session.clear()
            self.close()