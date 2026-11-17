from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup, QHeaderView, QTableWidgetItem, QMessageBox,
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, QPushButton,
    QDateEdit, QTextEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QHBoxLayout,
    QLabel
)
from PyQt6.QtCore import Qt, QDate
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.main_window_ui import Ui_MainWindow
from session import Session, Role
from db import client_repo, order_repo, report_repo
import hashlib


class OrderDialog(QDialog):
    """Диалог добавления/редактирования заказа."""

    def __init__(self, parent=None, order_data=None):
        super().__init__(parent)
        self.order_data = order_data
        self.setWindowTitle("Добавление заказа" if not order_data else "Редактирование заказа")
        self.setMinimumSize(500, 400)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.editVesselCode = QLineEdit()
        self.editVesselCode.setPlaceholderText("Например: VS-2026-001")
        form.addRow("Код судна:", self.editVesselCode)

        self.comboClient = QComboBox()
        self.comboClient.setMinimumWidth(250)
        form.addRow("Клиент:", self.comboClient)

        self.comboEmployee = QComboBox()
        self.comboEmployee.setMinimumWidth(250)
        form.addRow("Сотрудник:", self.comboEmployee)

        self.comboStatus = QComboBox()
        self.comboStatus.addItems(["Новый", "В работе", "Ожидает контроля", "Завершён"])
        form.addRow("Статус:", self.comboStatus)

        self.comboService = QComboBox()
        self.comboService.setMinimumWidth(250)
        form.addRow("Услуга:", self.comboService)

        self.spinPrice = QDoubleSpinBox()
        self.spinPrice.setRange(0, 999999)
        self.spinPrice.setDecimals(2)
        self.spinPrice.setSuffix(" руб.")
        form.addRow("Цена услуги:", self.spinPrice)

        self.btnAddService = QPushButton("Добавить услугу")
        self.btnAddService.clicked.connect(self._add_service)
        form.addRow("", self.btnAddService)

        self.lblServices = QLabel("Услуги не выбраны")
        self.lblServices.setWordWrap(True)
        form.addRow("Выбранные услуги:", self.lblServices)

        self._services = []  # список (service_id, service_name, price)

        layout.addLayout(form)

        self.btnBox = QHBoxLayout()
        self.btnSave = QPushButton("Сохранить")
        self.btnSave.setDefault(True)
        self.btnCancel = QPushButton("Отмена")
        self.btnCancel.clicked.connect(self.reject)
        self.btnBox.addWidget(self.btnSave)
        self.btnBox.addWidget(self.btnCancel)
        layout.addLayout(self.btnBox)

        self.btnSave.clicked.connect(self.accept)

        self._load_clients()
        self._load_employees()
        self._load_services()

        if order_data:
            self._fill_data(order_data)

    def _load_clients(self):
        clients = client_repo.get_all_clients()
        if clients:
            for c in clients:
                self.comboClient.addItem(c['name'], c['client_id'])

    def _load_employees(self):
        query = "SELECT employee_id, full_name FROM employees WHERE is_active = 1 ORDER BY full_name"
        employees = order_repo.execute_query(query)
        if employees:
            for e in employees:
                self.comboEmployee.addItem(e['full_name'], e['employee_id'])

    def _load_services(self):
        query = "SELECT service_id, service_name, price FROM services WHERE is_active = 1 ORDER BY service_name"
        services = order_repo.execute_query(query)
        if services:
            for s in services:
                self.comboService.addItem(f"{s['service_name']} ({s['price']} руб.)", s['service_id'])

    def _add_service(self):
        service_id = self.comboService.currentData()
        service_name = self.comboService.currentText()
        price = self.spinPrice.value()
        if service_id:
            self._services.append((service_id, service_name, price))
            names = ", ".join(s[1] for s in self._services)
            self.lblServices.setText(names)

    def _fill_data(self, data):
        self.editVesselCode.setText(data.get('vessel_code', ''))
        # Находим индекс клиента
        for i in range(self.comboClient.count()):
            if self.comboClient.itemData(i) == data.get('client_id'):
                self.comboClient.setCurrentIndex(i)
                break
        for i in range(self.comboEmployee.count()):
            if self.comboEmployee.itemData(i) == data.get('employee_id'):
                self.comboEmployee.setCurrentIndex(i)
                break
        index = self.comboStatus.findText(data.get('status', 'Новый'))
        if index >= 0:
            self.comboStatus.setCurrentIndex(index)

    def get_data(self):
        return {
            'vessel_code': self.editVesselCode.text().strip(),
            'client_id': self.comboClient.currentData(),
            'employee_id': self.comboEmployee.currentData(),
            'status': self.comboStatus.currentText(),
            'services': self._services
        }


class ClientDialog(QDialog):
    """Диалог добавления/редактирования клиента."""

    def __init__(self, parent=None, client_data=None):
        super().__init__(parent)
        self.client_data = client_data
        self.setWindowTitle("Добавление клиента" if not client_data else "Редактирование клиента")
        self.setMinimumSize(450, 350)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.comboType = QComboBox()
        self.comboType.addItems(["Физическое лицо", "Юридическое лицо"])
        form.addRow("Тип клиента:", self.comboType)

        self.editName = QLineEdit()
        self.editName.setPlaceholderText("ФИО или название компании")
        form.addRow("Название:", self.editName)

        self.editPhone = QLineEdit()
        self.editPhone.setPlaceholderText("+7 (999) 123-45-67")
        form.addRow("Телефон:", self.editPhone)

        self.editEmail = QLineEdit()
        self.editEmail.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.editEmail)

        self.editINN = QLineEdit()
        self.editINN.setPlaceholderText("ИНН (для юр. лиц)")
        form.addRow("ИНН:", self.editINN)

        layout.addLayout(form)

        self.btnBox = QHBoxLayout()
        self.btnSave = QPushButton("Сохранить")
        self.btnSave.setDefault(True)
        self.btnCancel = QPushButton("Отмена")
        self.btnCancel.clicked.connect(self.reject)
        self.btnBox.addWidget(self.btnSave)
        self.btnBox.addWidget(self.btnCancel)
        layout.addLayout(self.btnBox)

        self.btnSave.clicked.connect(self.accept)

        if client_data:
            self._fill_data(client_data)

    def _fill_data(self, data):
        self.editName.setText(data.get('name', ''))
        self.editPhone.setText(data.get('phone', ''))
        self.editEmail.setText(data.get('email', ''))
        if data.get('contact_person'):
            self.editName.setText(data.get('contact_person', ''))

    def get_data(self):
        return {
            'client_type': 'UL' if self.comboType.currentIndex() == 1 else 'FL',
            'phone': self.editPhone.text().strip(),
            'email': self.editEmail.text().strip(),
        }


class ResearchDialog(QDialog):
    """Диалог сохранения результата исследования."""

    def __init__(self, parent=None, service_name="", result_value=""):
        super().__init__(parent)
        self.setWindowTitle("Результат исследования")
        self.setMinimumSize(400, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.lblService = QLabel(service_name)
        self.lblService.setStyleSheet("font-weight: bold; font-size: 14px;")
        form.addRow("Услуга:", self.lblService)

        self.editResult = QLineEdit()
        self.editResult.setText(result_value)
        self.editResult.setPlaceholderText("Значение результата")
        form.addRow("Результат:", self.editResult)

        self.editConclusion = QTextEdit()
        self.editConclusion.setPlaceholderText("Заключение")
        self.editConclusion.setMaximumHeight(100)
        form.addRow("Заключение:", self.editConclusion)

        self.dateResult = QDateEdit()
        self.dateResult.setDate(QDate.currentDate())
        self.dateResult.setCalendarPopup(True)
        form.addRow("Дата:", self.dateResult)

        layout.addLayout(form)

        self.btnBox = QHBoxLayout()
        self.btnSave = QPushButton("Сохранить")
        self.btnSave.setDefault(True)
        self.btnCancel = QPushButton("Отмена")
        self.btnCancel.clicked.connect(self.reject)
        self.btnBox.addWidget(self.btnSave)
        self.btnBox.addWidget(self.btnCancel)
        layout.addLayout(self.btnBox)

        self.btnSave.clicked.connect(self.accept)

    def get_data(self):
        return {
            'result_value': self.editResult.text().strip(),
            'conclusion': self.editConclusion.toPlainText().strip(),
            'result_date': self.dateResult.date().toString("yyyy-MM-dd")
        }


class ReportDialog(QDialog):
    """Диалог создания отчёта."""

    def __init__(self, parent=None, order_code=""):
        super().__init__(parent)
        self.setWindowTitle("Создание отчёта")
        self.setMinimumSize(400, 250)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.lblOrder = QLabel(order_code)
        self.lblOrder.setStyleSheet("font-weight: bold; font-size: 14px;")
        form.addRow("Заказ:", self.lblOrder)

        self.editFilePath = QLineEdit()
        self.editFilePath.setPlaceholderText("Путь к файлу отчёта (опционально)")
        form.addRow("Файл:", self.editFilePath)

        layout.addLayout(form)

        self.btnBox = QHBoxLayout()
        self.btnSave = QPushButton("Создать отчёт")
        self.btnSave.setDefault(True)
        self.btnCancel = QPushButton("Отмена")
        self.btnCancel.clicked.connect(self.reject)
        self.btnBox.addWidget(self.btnSave)
        self.btnBox.addWidget(self.btnCancel)
        layout.addLayout(self.btnBox)

        self.btnSave.clicked.connect(self.accept)

    def get_data(self):
        return {
            'file_path': self.editFilePath.text().strip() or None
        }


class MainWindow(QMainWindow):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)

        user = Session.get_user()
        if not user:
            self.close()
            return

        self._apply_role_permissions()
        self._setup_sidebar()
        self._setup_tables()
        self._setup_home_tab()
        self._setup_orders_tab()
        self._setup_clients_tab()
        self._setup_research_tab()
        self._setup_reports_tab()

    def _setup_sidebar(self):
        sidebar_style = self.ui.sidebarFrame.styleSheet()
        if "QPushButton:checked" not in sidebar_style:
            sidebar_style += """
            QPushButton:checked {
                background-color: #154360;
                border-left: 4px solid #3498db;
                padding-left: 10px;
            }
            """
            self.ui.sidebarFrame.setStyleSheet(sidebar_style)

        self.nav_group = QButtonGroup(self)
        nav_buttons = [
            self.ui.btnHome, self.ui.btnOrders, self.ui.btnClients,
            self.ui.btnResearch, self.ui.btnReports
        ]

        for btn in nav_buttons:
            self.nav_group.addButton(btn)
            btn.setCheckable(True)

        self.ui.btnHome.setChecked(True)
        self.nav_group.buttonClicked.connect(self._on_nav_clicked)
        self.ui.btnExit.clicked.connect(self.logout)

    def _apply_role_permissions(self):
        self.ui.lblCurrentRole.setText(Session.get_role_display_name())
        self.ui.lblUsername.setText(Session.get_display_name())

        self.ui.btnOrders.setVisible(Session.has_permission("can_view_orders"))
        self.ui.btnResearch.setVisible(Session.has_permission("can_do_research"))
        self.ui.btnReports.setVisible(Session.has_permission("can_view_reports"))

        self.ui.btnAddOrder.setVisible(Session.has_permission("can_create_order"))
        self.ui.btnEditOrder.setVisible(Session.has_permission("can_view_orders"))
        self.ui.btnViewOrder.setVisible(Session.has_permission("can_view_orders"))

        self.ui.btnAddClient.setVisible(Session.has_permission("can_create_order"))
        self.ui.btnEditClient.setVisible(Session.has_permission("can_view_orders"))
        self.ui.btnViewClient.setVisible(Session.has_permission("can_view_orders"))

        self.ui.btnSaveResearchResult.setVisible(Session.has_permission("can_do_research"))
        self.ui.btnClearResearchResult.setVisible(Session.has_permission("can_do_research"))
        self.ui.btnViewResearchResult.setVisible(Session.has_permission("can_do_research"))

        self.ui.btnCreateReport.setVisible(Session.has_permission("can_create_reports"))
        self.ui.btnOpenReport.setVisible(Session.has_permission("can_view_reports"))
        self.ui.btnPrintReport.setVisible(Session.has_permission("can_view_reports"))

        current = self.ui.stackedWidget.currentWidget()
        visible_pages = [self.ui.pageHome]
        if Session.has_permission("can_view_orders"):
            visible_pages.append(self.ui.pageOrders)
            visible_pages.append(self.ui.pageClients)
        if Session.has_permission("can_do_research"):
            visible_pages.append(self.ui.pageResearch)
        if Session.has_permission("can_view_reports"):
            visible_pages.append(self.ui.pageReports)

        if current not in visible_pages:
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)
            self.ui.btnHome.setChecked(True)

    def _setup_tables(self):
        header_recent = self.ui.tableRecentOrders.horizontalHeader()
        header_recent.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_recent.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_recent.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_recent.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        header_orders = self.ui.tableOrders.horizontalHeader()
        header_orders.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_orders.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_orders.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        header_clients = self.ui.tableClients.horizontalHeader()
        header_clients.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_clients.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_clients.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_clients.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_clients.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        header_research = self.ui.tableResearchQueue.horizontalHeader()

        header_research.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_research.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_research.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_research.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        header_research.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)

        self.ui.tableResearchQueue.setColumnWidth(2, 150)
        self.ui.tableResearchQueue.setColumnWidth(3, 150)

        self.ui.tableResearchQueue.setWordWrap(True)

        header_report = self.ui.tableReportResearch.horizontalHeader()
        header_report.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        header_report.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        header_report.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)

        self.ui.tableReportResearch.setColumnWidth(0, 140)
        self.ui.tableReportResearch.setColumnWidth(1, 140)
        self.ui.tableReportResearch.setColumnWidth(2, 140)
        self.ui.tableReportResearch.setWordWrap(True)

        header_recent_rep = self.ui.tableRecentReports.horizontalHeader()
        header_recent_rep.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_recent_rep.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header_recent_rep.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_recent_rep.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        for table in [
            self.ui.tableRecentOrders,
            self.ui.tableOrders,
            self.ui.tableClients,
            self.ui.tableResearchQueue,
            self.ui.tableReportResearch,
            self.ui.tableRecentReports
        ]:
            table.verticalHeader().setVisible(False)

    def _on_nav_clicked(self, button):
        pages = {
            self.ui.btnHome: self.ui.pageHome,
            self.ui.btnOrders: self.ui.pageOrders,
            self.ui.btnClients: self.ui.pageClients,
            self.ui.btnResearch: self.ui.pageResearch,
            self.ui.btnReports: self.ui.pageReports
        }
        page = pages.get(button)
        if page:
            self.ui.stackedWidget.setCurrentWidget(page)

    def logout(self):
        Session.clear()
        self.close()

    def show_page(self, page):
        self.ui.stackedWidget.setCurrentWidget(page)

    def _setup_home_tab(self):
        self.ui.btnAllOrders.clicked.connect(self._go_to_orders)
        self._load_home_stats()
        self._load_recent_orders()

    def _setup_orders_tab(self):
        self.ui.btnAddOrder.clicked.connect(self._add_order)
        self.ui.btnEditOrder.clicked.connect(self._edit_order)
        self.ui.btnViewOrder.clicked.connect(self._view_order)
        self.ui.btnRefreshOrder.clicked.connect(self._refresh_orders_page)
        self.ui.btnSearchOrders.clicked.connect(self._search_orders)
        self.ui.btnResetOrderFilters.clicked.connect(self._reset_order_filters)
        self._load_orders_stats()
        self._load_orders_table()

    def _setup_clients_tab(self):
        self.ui.brnRefreshClients.clicked.connect(self._refresh_clients_page)
        self.ui.btnAddClient.clicked.connect(self._add_client)
        self.ui.btnEditClient.clicked.connect(self._edit_client)
        self.ui.btnViewClient.clicked.connect(self._view_client)
        self.ui.btnSearchClients.clicked.connect(self._search_clients)
        self.ui.btnResetClientFilters.clicked.connect(self._reset_client_filters)
        self._load_clients_to_table()
        self._load_clients_stats()

    def _setup_research_tab(self):
        self.ui.btnSaveResearchResult.clicked.connect(self._save_research)
        self.ui.btnClearResearchResult.clicked.connect(self._clear_research)
        self.ui.btnViewResearchResult.clicked.connect(self._view_research)
        self._load_research_queue()

    def _setup_reports_tab(self):
        self.ui.btnCreateReport.clicked.connect(self._create_report)
        self.ui.btnOpenReport.clicked.connect(self._open_report)
        self.ui.btnPrintReport.clicked.connect(self._print_report)

        self.ui.comboreportsOrder.currentIndexChanged.connect(self._on_report_order_changed)

        self._load_reports_combo()
        self._load_recent_reports()

    def _go_to_orders(self):
        self.ui.btnOrders.setChecked(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageOrders)

    # ==================== Заказы ====================

    def _add_order(self):
        dialog = OrderDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['vessel_code']:
                QMessageBox.warning(self, "Ошибка", "Введите код судна")
                return
            if not data['client_id']:
                QMessageBox.warning(self, "Ошибка", "Выберите клиента")
                return
            if not data['employee_id']:
                QMessageBox.warning(self, "Ошибка", "Выберите сотрудника")
                return

            order_id = order_repo.create_order(
                data['vessel_code'],
                data['client_id'],
                data['employee_id'],
                data['status']
            )
            if order_id:
                for service_id, service_name, price in data['services']:
                    order_repo.add_order_service(order_id, service_id, price)
                QMessageBox.information(self, "Успех", "Заказ успешно создан")
                self._load_orders_table()
                self._load_home_stats()
                self._load_recent_orders()
                self._load_reports_combo()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать заказ")

    def _edit_order(self):
        row = self.ui.tableOrders.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для редактирования")
            return

        order_id = int(self.ui.tableOrders.item(row, 0).data(Qt.ItemDataRole.UserRole) or 0)
        if not order_id:
            # Пытаемся найти по коду судна
            vessel_code = self.ui.tableOrders.item(row, 0).text()
            orders = order_repo.get_all_orders()
            for o in orders:
                if o['vessel_code'] == vessel_code:
                    order_id = o['order_id']
                    break

        if not order_id:
            QMessageBox.warning(self, "Ошибка", "Не удалось определить заказ")
            return

        orders = order_repo.get_all_orders()
        order_data = next((o for o in orders if o['order_id'] == order_id), None)
        if not order_data:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден")
            return

        dialog = OrderDialog(self, order_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if order_repo.update_order_status(order_id, data['status']):
                QMessageBox.information(self, "Успех", "Заказ обновлён")
                self._load_orders_table()
                self._load_home_stats()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось обновить заказ")

    def _view_order(self):
        row = self.ui.tableOrders.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для просмотра")
            return

        vessel_code = self.ui.tableOrders.item(row, 0).text()
        client = self.ui.tableOrders.item(row, 1).text()
        date = self.ui.tableOrders.item(row, 2).text()
        employee = self.ui.tableOrders.item(row, 3).text()
        status = self.ui.tableOrders.item(row, 4).text()

        msg = (
            f"Код судна: {vessel_code}\n"
            f"Клиент: {client}\n"
            f"Дата: {date}\n"
            f"Сотрудник: {employee}\n"
            f"Статус: {status}"
        )
        QMessageBox.information(self, "Детали заказа", msg)

    def _search_orders(self):
        text = self.ui.editOrderSearch.text().strip()
        if not text:
            self._load_orders_table()
            return

        orders = order_repo.search_orders(text)
        self._fill_orders_table(orders)

    def _reset_order_filters(self):
        self.ui.editOrderSearch.clear()
        self.ui.comboOrderStatus.setCurrentIndex(0)
        self._load_orders_table()

    def _refresh_orders_page(self):
        self._load_orders_stats()
        self._load_orders_table()

    def _fill_orders_table(self, orders):
        self.ui.tableOrders.setRowCount(0)
        if not orders:
            return

        self.ui.tableOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            item_id = QTableWidgetItem(str(order['order_id']))
            item_id.setData(Qt.ItemDataRole.UserRole, order['order_id'])
            item_id.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 0, item_id)

            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            self.ui.tableOrders.setItem(row_idx, 1, item_vessel)

            item_client = QTableWidgetItem(order['client_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 2, item_client)

            item_date = QTableWidgetItem(order['order_date'] or '')
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 3, item_date)

            item_employee = QTableWidgetItem(order['employee_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 4, item_employee)

            item_status = QTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 5, item_status)

            item_actions = QTableWidgetItem('')
            item_actions.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 6, item_actions)

    # ==================== Клиенты ====================

    def _add_client(self):
        dialog = ClientDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['phone']:
                QMessageBox.warning(self, "Ошибка", "Введите телефон")
                return

            client_id = client_repo.create_client(
                data['client_type'],
                data['phone'],
                data['email']
            )
            if client_id:
                QMessageBox.information(self, "Успех", "Клиент успешно добавлен")
                self._load_clients_to_table()
                self._load_clients_stats()
                self._load_reports_combo()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось добавить клиента")

    def _edit_client(self):
        row = self.ui.tableClients.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для редактирования")
            return

        client_id = int(self.ui.tableClients.item(row, 0).text())
        clients = client_repo.get_all_clients()
        client_data = next((c for c in clients if c['client_id'] == client_id), None)
        if not client_data:
            QMessageBox.warning(self, "Ошибка", "Клиент не найден")
            return

        dialog = ClientDialog(self, client_data)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            if not data['phone']:
                QMessageBox.warning(self, "Ошибка", "Введите телефон")
                return

            client_id_new = client_repo.create_client(
                data['client_type'],
                data['phone'],
                data['email']
            )
            if client_id_new:
                QMessageBox.information(self, "Успех", "Клиент обновлён")
                self._load_clients_to_table()
                self._load_clients_stats()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось обновить клиента")

    def _view_client(self):
        row = self.ui.tableClients.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента для просмотра")
            return

        client_id = int(self.ui.tableClients.item(row, 0).text())
        info = client_repo.get_client_info(client_id)
        if info:
            msg = (
                f"Название: {info.get('name', 'Не указано')}\n"
                f"Контактное лицо: {info.get('contact_person', 'Не указано')}\n"
                f"Телефон: {info.get('phone', 'Не указан')}\n"
                f"Email: {info.get('email', 'Не указана')}"
            )
            QMessageBox.information(self, "Информация о клиенте", msg)
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось загрузить информацию о клиенте")

    def _search_clients(self):
        text = self.ui.editClientsSearch.text().strip()
        if not text:
            self._load_clients_to_table()
            return

        clients = client_repo.search_clients(text)
        self._fill_clients_table(clients)

    def _reset_client_filters(self):
        self.ui.editClientsSearch.clear()
        self._load_clients_to_table()

    def _refresh_clients_page(self):
        self._load_clients_to_table()
        self._load_clients_stats()

    def _fill_clients_table(self, clients):
        self.ui.tableClients.setRowCount(0)
        if not clients:
            return

        self.ui.tableClients.setRowCount(len(clients))
        for row_idx, client in enumerate(clients):
            item_id = QTableWidgetItem(str(client['client_id']))
            item_id.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 0, item_id)

            item_name = QTableWidgetItem(client['name'])
            self.ui.tableClients.setItem(row_idx, 1, item_name)

            item_details = QTableWidgetItem(client['details'] or '')
            item_details.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 2, item_details)

            item_contact = QTableWidgetItem(client['contact_person'] or '')
            self.ui.tableClients.setItem(row_idx, 3, item_contact)

            item_orders = QTableWidgetItem("0")
            item_orders.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 4, item_orders)

    # ==================== Исследования ====================

    def _save_research(self):
        row = self.ui.tableResearchQueue.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите исследование из очереди")
            return

        order_service_id = int(self.ui.tableResearchQueue.item(row, 0).data(Qt.ItemDataRole.UserRole) or 0)
        service_name = self.ui.tableResearchQueue.item(row, 2).text()
        current_result = self.ui.tableResearchQueue.item(row, 4).text()

        dialog = ResearchDialog(self, service_name, current_result if current_result != 'Не выполнено' else '')
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            employee_id = Session.get_user_id()
            if not employee_id:
                QMessageBox.warning(self, "Ошибка", "Не определен текущий сотрудник")
                return

            result_id = report_repo.save_research_result(
                order_service_id,
                data['result_value'],
                data['conclusion'],
                data['result_date'],
                employee_id
            )
            if result_id:
                QMessageBox.information(self, "Успех", "Результат исследования сохранён")
                self._load_research_queue()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить результат")

    def _clear_research(self):
        row = self.ui.tableResearchQueue.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите исследование для очистки")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Очистить результат исследования?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Очистка результата (установка NULL)
            order_service_id = int(self.ui.tableResearchQueue.item(row, 0).data(Qt.ItemDataRole.UserRole) or 0)
            query = "UPDATE research_results SET result_value = NULL, conclusion = NULL WHERE order_service_id = %s"
            order_repo.execute_query(query, (order_service_id,))
            QMessageBox.information(self, "Успех", "Результат исследования очищен")
            self._load_research_queue()

    def _view_research(self):
        row = self.ui.tableResearchQueue.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите исследование для просмотра")
            return

        order_id = self.ui.tableResearchQueue.item(row, 1).text()
        vessel_code = self.ui.tableResearchQueue.item(row, 1).text() if self.ui.tableResearchQueue.item(row, 1) else ""
        service = self.ui.tableResearchQueue.item(row, 2).text()
        client = self.ui.tableResearchQueue.item(row, 3).text()
        result = self.ui.tableResearchQueue.item(row, 4).text()

        msg = (
            f"Заказ: {order_id}\n"
            f"Судно: {vessel_code}\n"
            f"Услуга: {service}\n"
            f"Клиент: {client}\n"
            f"Результат: {result}"
        )
        QMessageBox.information(self, "Результат исследования", msg)

    # ==================== Отчёты ====================

    def _create_report(self):
        order_id = self.ui.comboreportsOrder.currentData()
        if not order_id:
            QMessageBox.warning(self, "Ошибка", "Выберите заказ для отчёта")
            return

        orders = order_repo.get_all_orders()
        order_data = next((o for o in orders if o['order_id'] == order_id), None)
        vessel_code = order_data['vessel_code'] if order_data else ""

        dialog = ReportDialog(self, vessel_code)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            data = dialog.get_data()
            employee_id = Session.get_user_id()
            if not employee_id:
                QMessageBox.warning(self, "Ошибка", "Не определен текущий сотрудник")
                return

            report_id = report_repo.create_report(order_id, employee_id, data['file_path'])
            if report_id:
                QMessageBox.information(self, "Успех", f"Отчёт ОТЧ-{report_id:04d} создан")
                self._load_recent_reports()
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось создать отчёт")

    def _open_report(self):
        row = self.ui.tableRecentReports.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите отчёт для просмотра")
            return

        report_num = self.ui.tableRecentReports.item(row, 0).text()
        vessel_code = self.ui.tableRecentReports.item(row, 1).text()
        date = self.ui.tableRecentReports.item(row, 2).text()
        employee = self.ui.tableRecentReports.item(row, 3).text()

        msg = (
            f"Номер отчёта: {report_num}\n"
            f"Судно: {vessel_code}\n"
            f"Дата: {date}\n"
            f"Сотрудник: {employee}"
        )
        QMessageBox.information(self, "Отчёт", msg)

    def _print_report(self):
        row = self.ui.tableRecentReports.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите отчёт для печати")
            return

        report_num = self.ui.tableRecentReports.item(row, 0).text()
        reply = QMessageBox.question(
            self, "Печать",
            f"Отправить отчёт {report_num} на печать?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            QMessageBox.information(self, "Печать", f"Отчёт {report_num} отправлен на печать")

    # ==================== Загрузка данных ====================

    def _load_home_stats(self):
        stats = order_repo.get_home_stats()
        if not stats:
            return
        self.ui.lblOrderValue.setText(str(stats['total_orders']))
        self.ui.lblActiveOrdersValue.setText(str(stats['active_orders']))
        self.ui.lblClientsValue.setText(str(stats['total_clients']))
        self.ui.lblPendingChecksValue.setText(str(stats['pending_checks']))

    def _load_orders_stats(self):
        stats = order_repo.get_orders_stats()
        if not stats:
            return
        self.ui.lblTotalOrdersValue.setText(str(stats['total']))
        self.ui.lblOrdersInProgressValue.setText(str(stats['in_progress']))
        self.ui.lblOrdersPendingValue.setText(str(stats['pending']))
        self.ui.lblOrdersCompletedValue.setText(str(stats['completed']))

    def _load_clients_stats(self):
        stats = client_repo.get_clients_stats()
        if not stats:
            return
        self.ui.lblcardTotalClientsValue.setText(str(stats['total_clients']))
        self.ui.lblcardActiveClientsValue.setText(str(stats['active_clients']))
        self.ui.lblcardClientsWithOrdersValue.setText(str(stats['clients_with_orders']))

    def _load_recent_orders(self):
        orders = order_repo.get_recent_orders(limit=5)

        self.ui.tableRecentOrders.setRowCount(0)

        if not orders:
            print("ЗАКАЗОВ НЕТ")
            return

        self.ui.tableRecentOrders.setRowCount(len(orders))

        for row_idx, order in enumerate(orders):
            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            self.ui.tableRecentOrders.setItem(row_idx, 0, item_vessel)

            item_client = QTableWidgetItem(order['client_name'] or '')
            self.ui.tableRecentOrders.setItem(row_idx, 1, item_client)

            item_date = QTableWidgetItem(order['order_date'] or '')
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 2, item_date)

            item_status = QTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 3, item_status)

    def _load_orders_table(self):
        orders = order_repo.get_all_orders()

        self.ui.tableOrders.setRowCount(0)

        if not orders:
            return

        self.ui.tableOrders.setRowCount(len(orders))

        for row_idx, order in enumerate(orders):
            item_id = QTableWidgetItem(str(order['order_id']))
            item_id.setData(Qt.ItemDataRole.UserRole, order['order_id'])
            item_id.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 0, item_id)

            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            self.ui.tableOrders.setItem(row_idx, 1, item_vessel)

            item_client = QTableWidgetItem(order['client_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 2, item_client)

            item_date = QTableWidgetItem(order['order_date'] or '')
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 3, item_date)

            item_employee = QTableWidgetItem(order['employee_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 4, item_employee)

            item_status = QTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 5, item_status)

            item_actions = QTableWidgetItem('')
            item_actions.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 6, item_actions)

    def _load_clients_to_table(self):
        clients = client_repo.get_all_clients()

        self.ui.tableClients.setRowCount(0)

        if not clients:
            return

        self.ui.tableClients.setRowCount(len(clients))

        for row_idx, client in enumerate(clients):
            item_id = QTableWidgetItem(str(client['client_id']))
            item_id.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 0, item_id)

            item_name = QTableWidgetItem(client['name'])
            self.ui.tableClients.setItem(row_idx, 1, item_name)

            item_details = QTableWidgetItem(client['details'] or '')
            item_details.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 2, item_details)

            item_contact = QTableWidgetItem(client['contact_person'] or '')
            self.ui.tableClients.setItem(row_idx, 3, item_contact)

            item_orders = QTableWidgetItem("0")
            item_orders.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 4, item_orders)

    def _load_research_queue(self):
        research = report_repo.get_research_queue()

        self.ui.tableResearchQueue.setRowCount(0)

        if not research:
            return

        self.ui.tableResearchQueue.setRowCount(len(research))
        for row_idx, item in enumerate(research):
            item_order = QTableWidgetItem(str(item['order_id']))
            item_order.setData(Qt.ItemDataRole.UserRole, item['order_service_id'])
            item_order.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableResearchQueue.setItem(row_idx, 0, item_order)

            item_vessel = QTableWidgetItem(str(item['vessel_code']))
            self.ui.tableResearchQueue.setItem(row_idx, 1, item_vessel)

            item_service = QTableWidgetItem(item['service_name'])
            self.ui.tableResearchQueue.setItem(row_idx, 2, item_service)

            item_client = QTableWidgetItem(item['client_name'] or '')
            self.ui.tableResearchQueue.setItem(row_idx, 3, item_client)

            result_text = item['result_value'] if item['result_value'] else 'Не выполнено'
            item_result = QTableWidgetItem(result_text)
            item_result.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableResearchQueue.setItem(row_idx, 4, item_result)
        self.ui.tableResearchQueue.resizeRowsToContents()

    def _load_reports_combo(self):
        orders = order_repo.get_all_orders()

        self.ui.comboreportsOrder.blockSignals(True)
        self.ui.comboreportsOrder.clear()
        for order in orders:
            self.ui.comboreportsOrder.addItem(order['vessel_code'], order['order_id'])
        self.ui.comboreportsOrder.blockSignals(False)

        if orders:
            self._load_report_research_table(orders[0]['order_id'])

    def _on_report_order_changed(self, index):
        order_id = self.ui.comboreportsOrder.currentData()
        if order_id:
            self._load_report_research_table(order_id)

    def _load_report_research_table(self, order_id):
        rows = report_repo.get_report_research(order_id)

        self.ui.tableReportResearch.setRowCount(0)
        if not rows:
            return

        self.ui.tableReportResearch.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            self.ui.tableReportResearch.setItem(row_idx, 0, QTableWidgetItem(r['service_name']))
            self.ui.tableReportResearch.setItem(row_idx, 1, QTableWidgetItem(r['result_value'] or 'Не выполнено'))
            self.ui.tableReportResearch.setItem(row_idx, 2, QTableWidgetItem(r['conclusion'] or '-'))
        self.ui.tableReportResearch.resizeRowsToContents()

    def _load_recent_reports(self):
        rows = report_repo.get_recent_reports()

        self.ui.tableRecentReports.setRowCount(0)
        if not rows:
            return

        self.ui.tableRecentReports.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            self.ui.tableRecentReports.setItem(row_idx, 0, QTableWidgetItem(f"ОТЧ-{r['report_id']:04d}"))
            self.ui.tableRecentReports.setItem(row_idx, 1, QTableWidgetItem(r['vessel_code']))

            item_date = QTableWidgetItem(r['report_date'])
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentReports.setItem(row_idx, 2, item_date)

            self.ui.tableRecentReports.setItem(row_idx, 3, QTableWidgetItem(r['employee_name']))
