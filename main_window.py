"""Главное окно приложения ИС ОТК."""
from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup, QHeaderView, QTableWidgetItem,
    QMessageBox, QDialog, QDateEdit, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QAbstractItemView
)
from PyQt6 import QtGui, QtCore

from ui.main_window_ui import Ui_MainWindow
from ui.pages import (
    Ui_HomePage, Ui_OrdersPage, Ui_ClientsPage,
    Ui_ResearchPage, Ui_ReportsPage, Ui_EmployeesPage
)
from session import Session
from utils.formatting import format_date
from utils.files import open_file, print_file
from services.order_service import OrderService
from services.client_service import ClientService
from services.report_service import ReportService
from services.employee_service import EmployeeService
from services.service_service import ServiceService
from db import order_repo as _default_order_repo
from db import client_repo as _default_client_repo
from db import report_repo as _default_report_repo
from db import employee_repo as _default_employee_repo
from db import services_repo as _default_services_repo
from dialogs import (
    OrderDialog, ViewOrderDialog, ClientDialog,
    ClientEditDialog, ClientViewDialog, ServicesDialog,
    ResearchResultDialog
)
from pages.employees_page import EmployeesPage
from dialogs.log_widget import LogWidget
from widgets.base_table import make_item, populate_table
from widgets.styles import (
    SIDEBAR_BUTTON_STYLE,
    SIDEBAR_BUTTON_SECONDARY_STYLE,
    SIDEBAR_DANGER_BUTTON_STYLE,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Главное окно
# =============================================================================

class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self, app,
                 order_service: OrderService | None = None,
                 client_service: ClientService | None = None,
                 report_service: ReportService | None = None,
                 employee_service: EmployeeService | None = None):
        super().__init__()
        self.app = app

        # Dependency Injection
        self.order_service = order_service or OrderService(
            _default_order_repo, _default_client_repo, _default_services_repo
        )

        self.client_service = client_service or ClientService(_default_client_repo)
        self.report_service = report_service or ReportService(
            _default_report_repo, _default_order_repo
        )
        self.employee_service = employee_service or EmployeeService(_default_employee_repo)

        # Подключение уже выполнено в main.py через ConnectionDialog
        # Просто убеждаемся, что соединение активно
        try:
            from db.database import db
            db.get_connection()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка",
                f"Потеряно соединение с БД:\n{e}\n\nПерезапустите приложение."
            )
            self.close()
            return

        # Master UI (sidebar + stackedWidget + empty page containers)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        # Page UI classes (pyuic6-style) — fill the empty page containers
        self.ui_home = Ui_HomePage()
        self.ui_home.setupUi(self.ui.pageHome)

        self.ui_orders = Ui_OrdersPage()
        self.ui_orders.setupUi(self.ui.pageOrders)

        self.ui_clients = Ui_ClientsPage()
        self.ui_clients.setupUi(self.ui.pageClients)

        self.ui_research = Ui_ResearchPage()
        self.ui_research.setupUi(self.ui.pageResearch)

        self.ui_reports = Ui_ReportsPage()
        self.ui_reports.setupUi(self.ui.pageReports)

        self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)

        user = Session.get_user()
        if not user:
            self.close()
            return

        self._log_window = None
        self._apply_role_permissions()
        if self._is_admin():
            self._create_employees_page()
        self._setup_sidebar()
        self._setup_tables()
        self._connect_signals()

        # Синхронизация кнопок сайдбара со stackedWidget
        self.ui.stackedWidget.currentChanged.connect(self._on_page_changed)

        # Initial data loads
        self._load_home_stats()
        self._load_recent_orders()
        self._load_orders_stats()
        self._load_orders_table()
        self._load_clients_stats()
        self._load_clients_to_table()
        self._load_employees_combo()
        self._clear_all_research_info()
        self._load_research_queue()
        self._load_reports_combo()
        self._load_recent_reports()

        # Greeting: first login vs returning
        if Session.is_first_login():
            self.ui_home.lblWelcome.setText(
                "Добро пожаловать в информационную систему отдела технического контроля"
            )
            Session.mark_first_login_done()
        else:
            display_name = Session.get_display_name()
            self.ui_home.lblWelcome.setText(f"С возвращением, {display_name}!")

    def closeEvent(self, event):
        from db.database import db
        db.close()
        event.accept()

    def show_page(self, page_index: int):
        """Переключиться на указанную страницу."""
        logger.debug("Переключение на страницу %d (всего %d)", page_index, self.ui.stackedWidget.count())
        self.ui.stackedWidget.setCurrentIndex(page_index)

    def logout(self):
        Session.clear()
        self.close()

    # =========================================================================
    # НАВИГАЦИЯ И ОБЩЕЕ
    # =========================================================================

    def _setup_sidebar(self):
        """Настройка бокового меню и стилей кнопок — адаптивные, растягиваются по ширине sidebar."""
        from PyQt6.QtWidgets import QSizePolicy

        sidebar_frame = self.ui.sidebarFrame
        sidebar_layout = sidebar_frame.layout()

        sidebar_frame.setMaximumWidth(16777215)
        sidebar_frame.setMinimumWidth(200)

        inner_layout = None
        for i in range(sidebar_layout.count()):
            item = sidebar_layout.itemAt(i)
            if item and item.layout() and item.layout().objectName() == "sidebarLayout":
                inner_layout = item.layout()
                break

        nav_buttons = [
            self.ui.btnHome, self.ui.btnOrders, self.ui.btnClients,
            self.ui.btnResearch, self.ui.btnReports,
        ]
        for btn in nav_buttons:
            btn.setStyleSheet(SIDEBAR_BUTTON_STYLE)
            btn.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
            btn.setMinimumWidth(0)
            btn.setMinimumHeight(42)
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self.nav_group = QButtonGroup(self)
        for btn in nav_buttons:
            self.nav_group.addButton(btn)
            btn.setCheckable(True)
        self.ui.btnHome.setChecked(True)
        self.nav_group.buttonClicked.connect(self._on_nav_clicked)

        self.ui.btnExit.setStyleSheet(SIDEBAR_DANGER_BUTTON_STYLE)
        self.ui.btnExit.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.ui.btnExit.setMinimumWidth(0)
        self.ui.btnExit.setMinimumHeight(42)
        self.ui.btnExit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.ui.btnExit.clicked.connect(self.logout)

        is_admin = self._is_admin()
        if is_admin:
            self._add_logs_button()

        if is_admin:
            self._add_employees_button()

        if inner_layout:
            for i in range(inner_layout.count()):
                item = inner_layout.itemAt(i)
                if item and item.spacerItem():
                    item.spacerItem().changeSize(20, 0, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

    def _is_admin(self) -> bool:
        """Проверяет, является ли текущий пользователь администратором."""
        role = Session.get_role_display_name()
        return role in ('Администратор', 'admin', 'Administrator')

    def _add_logs_button(self):
        """Добавить кнопку просмотра логов в нижнюю часть sidebar (toggle)."""
        from PyQt6.QtWidgets import QSizePolicy

        self.btn_logs = QPushButton("📋 Логи")
        self.btn_logs.setStyleSheet(SIDEBAR_BUTTON_SECONDARY_STYLE)
        self.btn_logs.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.btn_logs.setMinimumWidth(0)
        self.btn_logs.setMinimumHeight(42)
        self.btn_logs.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_logs.setCheckable(True)
        self.btn_logs.clicked.connect(self._toggle_logs)

        sidebar_layout = self.ui.sidebarFrame.layout()
        if sidebar_layout:
            for i in range(sidebar_layout.count()):
                item = sidebar_layout.itemAt(i)
                if item and item.widget() == self.ui.btnExit:
                    sidebar_layout.insertWidget(i, self.btn_logs)
                    return

    def _add_employees_button(self):
        """Добавить кнопку управления сотрудниками перед кнопкой выхода."""
        from PyQt6.QtWidgets import QSizePolicy

        self.btn_employees = QPushButton("Сотрудники")
        self.btn_employees.setStyleSheet(SIDEBAR_BUTTON_STYLE)
        self.btn_employees.setCursor(QtGui.QCursor(QtCore.Qt.CursorShape.PointingHandCursor))
        self.btn_employees.setMinimumWidth(0)
        self.btn_employees.setMinimumHeight(42)
        self.btn_employees.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.btn_employees.setCheckable(True)
        self.btn_employees.clicked.connect(self._on_employees_clicked)

        self.nav_group.addButton(self.btn_employees)

        sidebar_layout = self.ui.sidebarFrame.layout()
        if sidebar_layout:
            for i in range(sidebar_layout.count()):
                item = sidebar_layout.itemAt(i)
                if item and item.widget() == self.ui.btnExit:
                    sidebar_layout.insertWidget(i, self.btn_employees)
                    return

    def _toggle_logs(self, checked: bool):
        """Toggle-показ/скрытие окна логов."""
        if checked:
            self._show_logs()
        else:
            self._hide_logs()

    def _show_logs(self):
        """Показать окно с логами приложения."""
        if not hasattr(self, '_log_window') or self._log_window is None:
            self._log_window = LogWidget(self)
            self._log_window.destroyed.connect(self._on_log_window_closed)
        self._log_window.show()
        self._log_window.raise_()
        self._log_window.activateWindow()

    def _hide_logs(self):
        """Скрыть окно логов."""
        if hasattr(self, '_log_window') and self._log_window:
            self._log_window.close()
            self._log_window = None

    def _on_log_window_closed(self):
        """Слот: окно логов закрыто пользователем (крестик)."""
        if hasattr(self, 'btn_logs') and self.btn_logs:
            self.btn_logs.blockSignals(True)
            self.btn_logs.setChecked(False)
            self.btn_logs.blockSignals(False)

    def _on_employees_clicked(self, checked: bool):
        """Обработка клика по кнопке 'Сотрудники'."""
        if checked:
            self.show_page(self.employees_page_index)

    def _on_page_changed(self, index):
        """Синхронизация состояния кнопок при смене страницы (вызов извне)."""
        current_widget = self.ui.stackedWidget.widget(index)
        if current_widget == getattr(self, 'employees_page', None):
            if hasattr(self, 'btn_employees') and self.btn_employees:
                self.btn_employees.blockSignals(True)
                self.btn_employees.setChecked(True)
                self.btn_employees.blockSignals(False)
            for btn in [self.ui.btnHome, self.ui.btnOrders, self.ui.btnClients,
                        self.ui.btnResearch, self.ui.btnReports]:
                btn.blockSignals(True)
                btn.setChecked(False)
                btn.blockSignals(False)

    def _apply_role_permissions(self):
        """Применение прав доступа в зависимости от роли пользователя."""
        self.ui_home.lblCurrentRole.setText(Session.get_role_display_name())
        self.ui_home.lblUsername.setText(Session.get_display_name())

        self.ui.btnOrders.setVisible(Session.has_permission("can_view_orders"))
        self.ui.btnResearch.setVisible(Session.has_permission("can_do_research"))
        self.ui.btnReports.setVisible(Session.has_permission("can_view_reports"))

        self.ui_orders.btnAddOrder.setVisible(Session.has_permission("can_create_order"))
        self.ui_orders.btnEditOrder.setVisible(Session.has_permission("can_view_orders"))
        self.ui_orders.btnViewOrder.setVisible(Session.has_permission("can_view_orders"))
        self.ui_clients.btnAddClient.setVisible(Session.has_permission("can_create_order"))
        self.ui_clients.btnEditClient.setVisible(Session.has_permission("can_view_orders"))
        self.ui_clients.btnViewClient.setVisible(Session.has_permission("can_view_orders"))
        self.ui_research.btnSaveResearchResult.setVisible(Session.has_permission("can_do_research"))
        self.ui_research.btnClearResearchResult.setVisible(Session.has_permission("can_do_research"))
        self.ui_research.btnViewResearchResult.setVisible(Session.has_permission("can_do_research"))
        self.ui_reports.btnAddReport.setVisible(Session.has_permission("can_create_reports"))
        self.ui_reports.btnViewReport.setVisible(Session.has_permission("can_view_reports"))
        self.ui_reports.btnExportReport.setVisible(Session.has_permission("can_view_reports"))

        current = self.ui.stackedWidget.currentWidget()
        visible_pages = [self.ui.pageHome]
        if Session.has_permission("can_view_orders"):
            visible_pages += [self.ui.pageOrders, self.ui.pageClients]
        if Session.has_permission("can_do_research"):
            visible_pages.append(self.ui.pageResearch)
        if Session.has_permission("can_view_reports"):
            visible_pages.append(self.ui.pageReports)
        if current not in visible_pages:
            self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome)
            self.ui.btnHome.setChecked(True)

    def _setup_tables(self):
        """Настройка заголовков таблиц и включение сортировки."""
        # Последние заказы (Home)
        h = self.ui_home.tableRecentOrders.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        h.setMinimumSectionSize(120)

        # Все заказы
        h = self.ui_orders.tableOrders.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.ui_orders.tableOrders.setWordWrap(True)

        # Клиенты
        h = self.ui_clients.tableClients.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.ui_clients.tableClients.setColumnWidth(1, 220)
        self.ui_clients.tableClients.setColumnWidth(3, 200)
        self.ui_clients.tableClients.setWordWrap(True)

        # Очередь исследований
        h = self.ui_research.tableResearchQueue.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setMinimumSectionSize(120)
        self.ui_research.tableResearchQueue.setWordWrap(True)

        # Исследования отчёта
        h = self.ui_reports.tableReportResearch.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        h.setMinimumSectionSize(120)
        self.ui_reports.tableReportResearch.setWordWrap(True)

        # Последние отчёты
        h = self.ui_reports.tableRecentReports.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        for table in [
            self.ui_home.tableRecentOrders, self.ui_orders.tableOrders,
            self.ui_clients.tableClients, self.ui_research.tableResearchQueue,
            self.ui_reports.tableReportResearch, self.ui_reports.tableRecentReports,
        ]:
            table.setSortingEnabled(True)
            table.verticalHeader().setVisible(False)

    def _connect_signals(self):
        """Подключение всех сигналов после настройки UI."""
        # Home
        self.ui_home.btnAllOrders.clicked.connect(self._go_to_orders)

        # Orders
        self.ui_orders.btnAddOrder.clicked.connect(self._add_order)
        self.ui_orders.btnEditOrder.clicked.connect(self._edit_order)
        self.ui_orders.btnViewOrder.clicked.connect(self._view_order)
        self.ui_orders.btnRefreshOrder.clicked.connect(self._load_orders_stats)
        self.ui_orders.btnSearchOrders.clicked.connect(self._search_orders)
        self.ui_orders.btnResetOrderFilters.clicked.connect(self._reset_filters)
        self.ui_orders.editOrderSearch.returnPressed.connect(self._search_orders)
        self.ui_orders.comboOrderStatus.currentIndexChanged.connect(self._search_orders)
        self.ui_orders.btnServices.clicked.connect(self._open_services_dialog)

        # Date filters for orders
        self.ui_orders.dateFrom.dateChanged.connect(self._search_orders)
        self.ui_orders.dateTo.dateChanged.connect(self._search_orders)

        # Clients
        self.ui_clients.brnRefreshClients.clicked.connect(self._refresh_clients_page)
        self.ui_clients.btnAddClient.clicked.connect(self._add_client)
        self.ui_clients.btnEditClient.clicked.connect(self._edit_client)
        self.ui_clients.btnViewClient.clicked.connect(self._view_client)
        self.ui_clients.btnSearchClients.clicked.connect(self._search_clients)
        self.ui_clients.btnResetClientFilters.clicked.connect(self._reset_client_filters)
        self.ui_clients.editClientsSearch.returnPressed.connect(self._search_clients)

        # Research
        self.ui_research.btnSaveResearchResult.clicked.connect(self._save_research)
        self.ui_research.btnClearResearchResult.clicked.connect(self._clear_research)
        self.ui_research.btnViewResearchResult.clicked.connect(self._view_research)
        self.ui_research.editResearchSearch.textChanged.connect(self._search_research)
        self.ui_research.comboResearchFilter.currentIndexChanged.connect(self._search_research)
        self.ui_research.tableResearchQueue.clicked.connect(self._on_research_row_selected)

        # Reports
        self.ui_reports.btnAddReport.clicked.connect(self._create_report)
        self.ui_reports.btnViewReport.clicked.connect(self._open_report)
        self.ui_reports.btnExportReport.clicked.connect(self._print_report)
        self.ui_reports.comboreportsOrder.currentIndexChanged.connect(self._on_report_order_changed)

        # Navigation
        self.ui.btnHome.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageHome))
        self.ui.btnOrders.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageOrders))
        self.ui.btnClients.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageClients))
        self.ui.btnResearch.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageResearch))
        self.ui.btnReports.clicked.connect(lambda: self.ui.stackedWidget.setCurrentWidget(self.ui.pageReports))

    def _on_nav_clicked(self, button):
        """Переключение страниц по клику на кнопку навигации."""
        pages = {
            self.ui.btnHome: self.ui.pageHome,
            self.ui.btnOrders: self.ui.pageOrders,
            self.ui.btnClients: self.ui.pageClients,
            self.ui.btnResearch: self.ui.pageResearch,
            self.ui.btnReports: self.ui.pageReports,
        }
        page = pages.get(button)
        if page:
            self.ui.stackedWidget.setCurrentWidget(page)
            if hasattr(self, 'btn_employees') and self.btn_employees:
                self.btn_employees.blockSignals(True)
                self.btn_employees.setChecked(False)
                self.btn_employees.blockSignals(False)

    # =========================================================================
    # HOME — Главная страница
    # =========================================================================

    def _go_to_orders(self):
        self.ui.btnOrders.setChecked(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageOrders)

    def _load_home_stats(self):
        stats = self.order_service.get_home_stats()
        if not stats:
            return
        self.ui_home.lblOrderValue.setText(str(stats['total_orders']))
        self.ui_home.lblActiveOrdersValue.setText(str(stats['active_orders']))
        self.ui_home.lblClientsValue.setText(str(stats['total_clients']))
        self.ui_home.lblPendingChecksValue.setText(str(stats['pending_checks']))

    def _load_recent_orders(self):
        orders = self.order_service.get_recent_orders(limit=5)
        self._populate_recent_orders_table(orders)

    def _populate_recent_orders_table(self, orders):
        populate_table(self.ui_home.tableRecentOrders, orders, self._fill_recent_order_row)

    @staticmethod
    def _fill_recent_order_row(table, row_idx, order):
        table.setItem(row_idx, 0, make_item(order['vessel_code']))
        table.setItem(row_idx, 1, make_item(order['client_name']))
        table.setItem(row_idx, 2, make_item(
            format_date(order['order_date']), center=True,
            sort_value=order['order_date']))
        table.setItem(row_idx, 3, make_item(order['status'], center=True))

    # =========================================================================
    # ORDERS — Заказы
    # =========================================================================

    def _load_orders_stats(self):
        stats = self.order_service.get_orders_stats()
        if not stats:
            return
        self.ui_orders.lblTotalOrdersValue.setText(str(stats['total']))
        self.ui_orders.lblOrdersInProgressValue.setText(str(stats['in_progress']))
        self.ui_orders.lblOrdersPendingValue.setText(str(stats['pending']))
        self.ui_orders.lblOrdersCompletedValue.setText(str(stats['completed']))

    def _load_orders_table(self):
        orders = self.order_service.get_all_orders()
        self._populate_orders_table(orders)

    def _populate_orders_table(self, orders):
        populate_table(self.ui_orders.tableOrders, orders, self._fill_order_row)

    @staticmethod
    def _fill_order_row(table, row_idx, order):
        table.setItem(row_idx, 0, make_item(
            order['vessel_code'], sort_value=order['order_id'],
            user_data=order['order_id']))
        table.setItem(row_idx, 1, make_item(order.get('client_name')))
        table.setItem(row_idx, 2, make_item(
            format_date(order.get('order_date')), center=True,
            sort_value=order.get('order_date')))
        table.setItem(row_idx, 3, make_item(order.get('employee_name')))
        table.setItem(row_idx, 4, make_item(order.get('status'), center=True))
        table.setItem(row_idx, 5, make_item('-', center=True))
        table.setItem(row_idx, 6, make_item('', center=True))

    def _search_orders(self):
        """Поиск заказов: текст + статус + диапазон дат."""
        query = self.ui_orders.editOrderSearch.text().strip().lower()
        status = self.ui_orders.comboOrderStatus.currentText()

        orders = self.order_service.get_all_orders()
        filtered = []
        for o in orders:
            match_text = True
            if query:
                search_str = (
                    f"{o.get('vessel_code', '')} "
                    f"{o.get('client_name', '')} "
                    f"{o.get('order_id', '')}"
                ).lower()
                match_text = query in search_str

            match_status = True
            if status and status != "Все статусы":
                match_status = (o.get('status') == status)

            match_date = True
            order_date = o.get('order_date')
            if order_date:
                if isinstance(order_date, datetime):
                    order_date = order_date.date()
                match_date = (
                    order_date >= self.ui_orders.dateFrom.date().toPyDate()
                    and order_date <= self.ui_orders.dateTo.date().toPyDate()
                )

            if match_text and match_status and match_date:
                filtered.append(o)

        self._populate_orders_table(filtered)

    def _reset_filters(self):
        self.ui_orders.editOrderSearch.clear()
        self.ui_orders.comboOrderStatus.setCurrentIndex(0)
        self.ui_orders.dateFrom.setDate(QDate.currentDate().addMonths(-1))
        self.ui_orders.dateTo.setDate(QDate.currentDate())
        self._load_orders_table()

    def _add_order(self):
        dlg = OrderDialog(self, order_id=None,
                          order_service=self.order_service,
                          client_service=self.client_service,
                          service_service=ServiceService(_default_services_repo))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_orders_table()
            self._load_orders_stats()
            self._load_home_stats()
            self._load_recent_orders()
            self._load_reports_combo()

    def _edit_order(self):
        row = self.ui_orders.tableOrders.currentRow()
        if row < 0:
            QMessageBox.information(self, "Редактирование", "Выберите заказ в таблице.")
            return
        order_id = self._get_selected_order_id(row)
        if not order_id:
            return
        dlg = OrderDialog(self, order_id=order_id,
                          order_service=self.order_service,
                          client_service=self.client_service,
                          service_service=ServiceService(_default_services_repo))
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_orders_table()
            self._load_orders_stats()
            self._load_recent_orders()
            self._load_reports_combo()

    def _view_order(self):
        row = self.ui_orders.tableOrders.currentRow()
        if row < 0:
            QMessageBox.information(self, "Просмотр", "Выберите заказ в таблице.")
            return
        order_id = self._get_selected_order_id(row)
        if not order_id:
            return
        dlg = ViewOrderDialog(self, order_id=order_id,
                              order_service=self.order_service)
        dlg.exec()

    def _get_selected_order_id(self, row: int) -> int | None:
        item = self.ui_orders.tableOrders.item(row, 0)
        if item is None:
            return None
        oid = item.data(Qt.ItemDataRole.UserRole)
        if oid:
            return int(oid)
        vessel = item.text()
        orders = self.order_service.get_all_orders()
        for o in orders:
            if o.get('vessel_code') == vessel:
                return o['order_id']
        return None

    def _open_services_dialog(self):
        """Открыть диалог управления услугами."""
        dlg = ServicesDialog(self, service_service=ServiceService(_default_services_repo))
        dlg.exec()

    # =========================================================================
    # CLIENTS — Клиенты
    # =========================================================================

    def _load_clients_stats(self):
        stats = self.client_service.get_clients_stats()
        if not stats:
            return
        self.ui_clients.lblcardTotalClientsValue.setText(str(stats['total_clients']))
        self.ui_clients.lblcardActiveClientsValue.setText(str(stats['active_clients']))
        self.ui_clients.lblcardClientsWithOrdersValue.setText(str(stats['clients_with_orders']))

    def _load_clients_to_table(self):
        clients = self.client_service.get_all_clients()
        orders_count = self.client_service.get_clients_orders_count()
        self._populate_clients_table(clients, orders_count)

    def _populate_clients_table(self, clients, orders_count=None):
        if orders_count is None:
            orders_count = self.client_service.get_clients_orders_count()

        def fill_row(table, row_idx, c):
            count = orders_count.get(c['client_id'], 0)
            table.setItem(row_idx, 0, make_item(
                c['client_id'], center=True, sort_value=c['client_id']))
            table.setItem(row_idx, 1, make_item(c.get('name')))
            table.setItem(row_idx, 2, make_item(c.get('details'), center=True))
            table.setItem(row_idx, 3, make_item(c.get('contact_person')))
            table.setItem(row_idx, 4, make_item(count, center=True, sort_value=count))

        populate_table(self.ui_clients.tableClients, clients, fill_row)

    def _search_clients(self):
        query = self.ui_clients.editClientsSearch.text().strip().lower()
        if not query:
            self._load_clients_to_table()
            return
        clients = self.client_service.get_all_clients()
        filtered = [
            c for c in clients
            if query in (
                f"{c.get('name', '')} "
                f"{c.get('details', '')} "
                f"{c.get('contact_person', '')}"
            ).lower()
        ]
        self._populate_clients_table(filtered)

    def _reset_client_filters(self):
        self.ui_clients.editClientsSearch.clear()
        self._load_clients_to_table()

    def _add_client(self):
        dlg = ClientDialog(self, initial_type="ЮЛ",
                           client_service=self.client_service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_clients_page()
            self._load_home_stats()

    def _edit_client(self):
        row = self.ui_clients.tableClients.currentRow()
        if row < 0:
            QMessageBox.information(self, "Редактирование", "Выберите клиента в таблице.")
            return
        client_id = int(self.ui_clients.tableClients.item(row, 0).text())
        dlg = ClientEditDialog(self, client_id,
                               client_service=self.client_service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_clients_page()

    def _view_client(self):
        row = self.ui_clients.tableClients.currentRow()
        if row < 0:
            QMessageBox.information(self, "Просмотр", "Выберите клиента в таблице.")
            return
        client_id = int(self.ui_clients.tableClients.item(row, 0).text())
        dlg = ClientViewDialog(self, client_id,
                               client_service=self.client_service)
        dlg.exec()

    def _refresh_clients_page(self):
        self._load_clients_to_table()
        self._load_clients_stats()

    # =========================================================================
    # RESEARCH — Исследования
    # =========================================================================

    def _load_employees_combo(self):
        """Загрузить список активных сотрудников в comboResearchEmployee."""
        employees = self.employee_service.get_employees()
        self.ui_research.comboResearchEmployee.blockSignals(True)
        self.ui_research.comboResearchEmployee.clear()
        for emp in employees:
            self.ui_research.comboResearchEmployee.addItem(emp['full_name'], emp['employee_id'])
        self.ui_research.comboResearchEmployee.blockSignals(False)

    def _on_research_row_selected(self, index):
        """Обработка клика по строке в таблице исследований."""
        row = index.row()
        if row < 0:
            return

        order_id = self.ui_research.tableResearchQueue.item(row, 0).text()
        vessel_code = self.ui_research.tableResearchQueue.item(row, 1).text()
        service_name = self.ui_research.tableResearchQueue.item(row, 2).text()
        client_name = self.ui_research.tableResearchQueue.item(row, 3).text()

        self.ui_research.lblResearchOrderValue.setText(order_id)
        self.ui_research.lblResearchVesselValue.setText(vessel_code)
        self.ui_research.lblResearchClientValue.setText(client_name)
        self.ui_research.lblResearchServiceValue.setText(service_name)

        item = self.ui_research.tableResearchQueue.item(row, 0)
        order_service_id = item.data(Qt.ItemDataRole.UserRole)
        if order_service_id:
            self._current_order_service_id = order_service_id
            self._load_existing_research_result(order_service_id)

    def _load_existing_research_result(self, order_service_id: int):
        """Загрузить существующий результат исследования в поля."""
        result = self.report_service.get_research_result(order_service_id)
        if result:
            self.ui_research.editResearchResultValue.setText(result.get('result_value', '') or '')
            self.ui_research.textResearchConclusion.setPlainText(result.get('conclusion', '') or '')
            if result.get('result_date'):
                result_date = result['result_date']
                if hasattr(result_date, 'toPyDate'):
                    self.ui_research.dateResearchResult.setDate(result_date)
                else:
                    self.ui_research.dateResearchResult.setDate(
                        QDate.fromString(str(result_date), 'yyyy-MM-dd'))
            if result.get('employee_id'):
                for i in range(self.ui_research.comboResearchEmployee.count()):
                    if self.ui_research.comboResearchEmployee.itemData(i) == result['employee_id']:
                        self.ui_research.comboResearchEmployee.setCurrentIndex(i)
                        break
        else:
            self._clear_research_details()

    def _clear_research_details(self):
        """Очистить только поля результата исследования."""
        self.ui_research.editResearchResultValue.clear()
        self.ui_research.textResearchConclusion.clear()
        self.ui_research.dateResearchResult.setDate(QDate.currentDate())

    def _clear_all_research_info(self):
        """Очистить всё, включая информационные метки."""
        self.ui_research.lblResearchOrderValue.setText('')
        self.ui_research.lblResearchVesselValue.setText('')
        self.ui_research.lblResearchClientValue.setText('')
        self.ui_research.lblResearchServiceValue.setText('')
        self._clear_research_details()
        self._current_order_service_id = None

    def _save_research(self):
        """Сохранить результат исследования."""
        if not hasattr(self, '_current_order_service_id') or not self._current_order_service_id:
            QMessageBox.warning(self, "Ошибка", "Выберите исследование из списка.")
            return

        result_value = self.ui_research.editResearchResultValue.text().strip()
        conclusion = self.ui_research.textResearchConclusion.toPlainText().strip()
        result_date = self.ui_research.dateResearchResult.date().toPyDate()
        employee_id = self.ui_research.comboResearchEmployee.currentData()

        if not result_value:
            QMessageBox.warning(self, "Ошибка", "Введите результат исследования.")
            return

        try:
            self.report_service.save_research_result(
                order_service_id=self._current_order_service_id,
                employee_id=employee_id,
                result_value=result_value,
                conclusion=conclusion,
                result_date=result_date
            )
            QMessageBox.information(self, "Готово", "Результат исследования сохранён.")
            self._load_research_queue()
            self._refresh_reports_page()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить результат:\n{e}")

    def _refresh_reports_page(self):
        """Обновить страницу отчётов."""
        self._load_reports_combo()

        order_id = self.ui_reports.comboreportsOrder.currentData()
        if order_id:
            self._load_report_research_table(order_id)
            self._update_report_preview(order_id)

        self._load_recent_reports()

    def _clear_research(self):
        """Очистить поля ввода результата."""
        self.ui_research.editResearchResultValue.clear()
        self.ui_research.textResearchConclusion.clear()
        self.ui_research.dateResearchResult.setDate(QDate.currentDate())

    def _view_research(self):
        """Просмотреть результат исследования."""
        if not hasattr(self, '_current_order_service_id') or not self._current_order_service_id:
            QMessageBox.warning(self, "Просмотр", "Выберите исследование из списка.")
            return

        row = self.ui_research.tableResearchQueue.currentRow()
        research_info = {
            'order_id': self.ui_research.tableResearchQueue.item(row, 0).text(),
            'vessel_code': self.ui_research.tableResearchQueue.item(row, 1).text(),
            'service_name': self.ui_research.tableResearchQueue.item(row, 2).text(),
            'client_name': self.ui_research.tableResearchQueue.item(row, 3).text(),
        }

        dlg = ResearchResultDialog(
            self,
            order_service_id=self._current_order_service_id,
            research_info=research_info,
            report_service=self.report_service,
            employee_service=self.employee_service,
        )
        dlg.exec()

    def _load_research_queue(self):
        """Загрузка очереди исследований."""
        research = self.report_service.get_research_queue()
        self._populate_research_table(research)

    def _populate_research_table(self, research):
        """Заполнить таблицу исследований."""
        populate_table(self.ui_research.tableResearchQueue, research, self._fill_research_row)
        self.ui_research.tableResearchQueue.resizeRowsToContents()

    @staticmethod
    def _fill_research_row(table, row_idx, item):
        table.setItem(row_idx, 0, make_item(
            item['order_id'], center=True, sort_value=item['order_id'],
            user_data=item['order_service_id']))
        table.setItem(row_idx, 1, make_item(item['vessel_code']))
        table.setItem(row_idx, 2, make_item(item['service_name']))
        table.setItem(row_idx, 3, make_item(item['client_name']))
        table.setItem(row_idx, 4, make_item(
            item['result_value'] or 'Не выполнено', center=True))

    def _search_research(self):
        """Фильтрация очереди исследований по тексту и наличию результата."""
        query = self.ui_research.editResearchSearch.text().strip().lower()
        filter_mode = self.ui_research.comboResearchFilter.currentIndex()

        research = self.report_service.get_research_queue()
        filtered = []
        for item in research:
            match_text = True
            if query:
                search_str = (
                    f"{item.get('vessel_code', '')} "
                    f"{item.get('service_name', '')} "
                    f"{item.get('client_name', '')} "
                    f"{item.get('order_id', '')}"
                ).lower()
                match_text = query in search_str

            match_result = True
            if filter_mode == 1:
                match_result = not bool(item.get('result_value'))
            elif filter_mode == 2:
                match_result = bool(item.get('result_value'))

            if match_text and match_result:
                filtered.append(item)

        self._populate_research_table(filtered)

    # =========================================================================
    # REPORTS — Отчёты
    # =========================================================================

    def _load_reports_combo(self):
        orders = self.order_service.get_all_orders()
        self.ui_reports.comboreportsOrder.blockSignals(True)
        self.ui_reports.comboreportsOrder.clear()
        for order in orders:
            self.ui_reports.comboreportsOrder.addItem(order['vessel_code'], order['order_id'])
        self.ui_reports.comboreportsOrder.blockSignals(False)
        if orders:
            self._load_report_research_table(orders[0]['order_id'])

    def _on_report_order_changed(self, index):
        order_id = self.ui_reports.comboreportsOrder.currentData()
        if order_id:
            self._load_report_research_table(order_id)
            self._update_report_preview(order_id)

    def _load_report_research_table(self, order_id):
        rows = self.report_service.get_report_research(order_id)
        def fill_row(table, row_idx, r):
            table.setItem(row_idx, 0, make_item(r['service_name']))
            table.setItem(row_idx, 1, make_item(r['result_value'] or 'Не выполнено'))
            table.setItem(row_idx, 2, make_item(r['conclusion'] or '-'))

        populate_table(self.ui_reports.tableReportResearch, rows, fill_row)
        self.ui_reports.tableReportResearch.resizeRowsToContents()

    def _update_report_preview(self, order_id: int):
        """Обновить предпросмотр отчёта."""
        order = self.order_service.get_order(order_id)
        if not order:
            return

        self._preview_order_id = order_id
        self._current_report_path = None

        existing = self.report_service.get_report_by_order(order_id)
        if existing:
            report_num = f"ОТЧ-{existing['report_id']:04d}"
            report_date = format_date(existing['report_date'])
            self._current_report_path = existing.get('file_path')
        else:
            next_id = self.report_service.get_next_report_number()
            report_num = f"ОТЧ-{next_id:04d}"
            report_date = datetime.now().strftime('%d.%m.%Y')

        client_name = order.get('client_name', '')
        vessel_code = order.get('vessel_code', '')
        order_date = format_date(order.get('order_date'))

        research_rows = self.report_service.get_report_research(order_id)

        table_rows_html = ''
        if research_rows:
            for idx, r in enumerate(research_rows, 1):
                bg = "#F0F5FA" if idx % 2 == 0 else "#FFFFFF"
                service = r.get('service_name', '')
                result = r.get('result_value') or 'Не выполнено'
                conclusion = r.get('conclusion') or '-'
                table_rows_html += f"""
                    <tr style="background-color: {bg};">
                        <td style="text-align: center;">{idx}</td>
                        <td>{service}</td>
                        <td>{result}</td>
                        <td>{conclusion}</td>
                    </tr>
                """
        else:
            table_rows_html = '<tr><td colspan="4" style="text-align: center;">Исследования не назначены</td></tr>'

        conclusions = [r.get('conclusion') for r in research_rows if r.get('conclusion')]
        if conclusions:
            conclusion_text = "Заключение: " + "; ".join(conclusions)
        elif research_rows and all(r.get('result_value') for r in research_rows):
            conclusion_text = "Заключение: все исследования выполнены."
        else:
            conclusion_text = "Заключение: часть исследований ещё не выполнена."

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    font-size: 11pt;
                    color: #000000;
                    margin: 40px;
                    line-height: 1.6;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .org-name {{
                    font-size: 16pt;
                    font-weight: bold;
                    margin-bottom: 20px;
                }}
                .report-title {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #174A7E;
                    margin-bottom: 30px;
                }}
                .info-block {{
                    margin-bottom: 15px;
                }}
                .table-title {{
                    text-align: center;
                    font-size: 12pt;
                    font-weight: bold;
                    color: #174A7E;
                    margin: 30px 0 20px 0;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th {{
                    background-color: #174A7E;
                    color: #FFFFFF;
                    padding: 10px 8px;
                    text-align: left;
                    font-weight: bold;
                    border: 1px solid #D2DFEC;
                }}
                td {{
                    padding: 8px;
                    border: 1px solid #D2DFEC;
                    vertical-align: middle;
                }}
                .conclusion {{
                    margin-top: 30px;
                    font-size: 11pt;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <div class="org-name">ООО "СПбЦ "ЭЛМА""</div>
                <div class="report-title">ОТЧЁТ О РЕЗУЛЬТАТАХ ИССЛЕДОВАНИЙ</div>
            </div>

            <div class="info-block">
                <strong>Номер отчёта:</strong> {report_num} от {report_date}
            </div>

            <div class="info-block">
                <strong>Заказчик:</strong> {client_name}
            </div>

            <div class="info-block">
                <strong>Номер заказа:</strong> {vessel_code} &nbsp;&nbsp;&nbsp;
                <strong>Дата:</strong> {order_date}
            </div>

            <div class="table-title">Перечень выполненных исследований:</div>

            <table>
                <thead>
                    <tr>
                        <th style="width: 5%;">№</th>
                        <th style="width: 40%;">Исследование</th>
                        <th style="width: 25%;">Результат</th>
                        <th style="width: 30%;">Заключение</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows_html}
                </tbody>
            </table>

            <div class="conclusion">
                {conclusion_text}
            </div>
        </body>
        </html>
        """

        self.ui_reports.reportPreviewBrowser.setHtml(html)

    def _fill_client_info_panel(self, order: dict):
        """Заполняет левый блок «Информация о клиенте», если метки существуют."""
        client_name = order.get('client_name') or ''
        details = ''
        try:
            info = self.client_service.get_client_details(order['client_id'])
            if info:
                parts = [info.get('phone'), info.get('email')]
                details = ", ".join(p for p in parts if p)
        except Exception:
            pass

        for name in ("lblReportClientName", "lblReportClientValue",
                     "lblClientNameValue", "lblReportClient"):
            if hasattr(self.ui, name):
                getattr(self.ui, name).setText(client_name)
        for name in ("lblReportClientContact", "lblReportClientContactValue",
                     "lblClientContactValue"):
            if hasattr(self.ui, name):
                getattr(self.ui, name).setText(details or "—")

    def _load_recent_reports(self):
        """Загрузить отчёты из папки reports."""
        reports_dir = Path(__file__).parent / 'reports'
        if not reports_dir.exists():
            self.ui_reports.tableRecentReports.setRowCount(0)
            return

        pdf_files = [f for f in reports_dir.glob('*.pdf') if f.is_file()]
        if not pdf_files:
            self.ui_reports.tableRecentReports.setRowCount(0)
            return

        pdf_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        self.ui_reports.tableRecentReports.setSortingEnabled(False)
        self.ui_reports.tableRecentReports.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.ui_reports.tableRecentReports.setRowCount(len(pdf_files))

        for row_idx, pdf_file in enumerate(pdf_files):
            filename = pdf_file.stem  # ОТЧ-0013

            match = re.match(r'ОТЧ-(\d+)', filename)
            if match:
                report_id = int(match.group(1))
                report_num = f"ОТЧ-{report_id:04d}"
            else:
                report_num = f"ОТЧ-{row_idx + 1:04d}"
                report_id = None

            order_number = 'Неизвестно'
            employee_name = 'Неизвестно'
            report_date = ''

            if report_id:
                try:
                    rep = self.report_service.get_report(report_id)
                    if rep:
                        order_number = rep.get('vessel_code') or 'Неизвестно'
                        employee_name = rep.get('employee_name') or 'Неизвестно'
                        report_date_obj = rep.get('report_date')
                        if report_date_obj:
                            if hasattr(report_date_obj, 'strftime'):
                                report_date = report_date_obj.strftime('%d.%m.%Y')
                            else:
                                report_date = str(report_date_obj)
                except Exception as exc:
                    logger.debug("Ошибка получения данных отчёта %s: %s", report_id, exc)

            if not report_date:
                file_time = datetime.fromtimestamp(pdf_file.stat().st_mtime)
                report_date = file_time.strftime('%d.%m.%Y %H:%M:%S')

            item_report_id = QTableWidgetItem(report_num)
            item_report_id.setData(Qt.ItemDataRole.UserRole, str(pdf_file))
            self.ui_reports.tableRecentReports.setItem(row_idx, 0, item_report_id)

            self.ui_reports.tableRecentReports.setItem(row_idx, 1, QTableWidgetItem(str(order_number)))
            self.ui_reports.tableRecentReports.setItem(row_idx, 2, QTableWidgetItem(report_date))
            self.ui_reports.tableRecentReports.setItem(row_idx, 3, QTableWidgetItem(employee_name))

        self.ui_reports.tableRecentReports.setSortingEnabled(True)

    def _create_report(self):
        """Формирует PDF по заказу из предпросмотра."""
        order_id = getattr(self, '_preview_order_id', None) \
            or self.ui_reports.comboreportsOrder.currentData()
        if not order_id:
            QMessageBox.warning(self, "Формирование отчёта", "Выберите заказ.")
            return

        try:
            report_id = self.report_service.create_report(
                order_id, Session.get_user_id(), None)

            from report_generator import generate_report_pdf
            filepath = generate_report_pdf(
                order_id, report_id,
                order_service=self.order_service,
                report_service=self.report_service,
            )

            self.report_service.update_report_path(report_id, filepath)

            self._current_report_path = filepath

            self._load_recent_reports()
            QMessageBox.information(
                self, "Отчёт сформирован",
                f"Отчёт ОТЧ-{report_id:04d} сохранён.\nФайл: {filepath}")
        except ImportError:
            QMessageBox.critical(self, "Ошибка",
                                "Не установлена библиотека reportlab.\n"
                                "Выполните: pip install reportlab")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сформировать отчёт:\n{e}")

    def _resolve_report_path(self) -> str | None:
        """Определяет, какой файл открывать/печатать.
        Приоритет: выбранный в таблице отчёт → созданный в предпросмотре → отчёт по заказу."""
        row = self.ui_reports.tableRecentReports.currentRow()
        if row >= 0:
            item = self.ui_reports.tableRecentReports.item(row, 0)
            if item:
                try:
                    report_id = int(item.text().replace("ОТЧ-", ""))
                    rep = self.report_service.get_report(report_id)
                    if rep and rep.get('file_path'):
                        return rep['file_path']
                except ValueError:
                    pass

        if self._current_report_path:
            return self._current_report_path

        order_id = self.ui_reports.comboreportsOrder.currentData()
        if order_id:
            rep = self.report_service.get_report_by_order(order_id)
            if rep and rep.get('file_path'):
                return rep['file_path']
        return None

    def _open_report(self):
        path = self._resolve_report_path()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Открытие отчёта",
                                "Файл отчёта не найден.\nСначала нажмите «Сформировать отчёт».")
            return
        try:
            open_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def _print_report(self):
        path = self._resolve_report_path()
        if not path or not os.path.exists(path):
            QMessageBox.warning(self, "Печать отчёта",
                                "Файл отчёта не найден.\nСначала нажмите «Сформировать отчёт».")
            return
        try:
            print_file(path)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить на печать:\n{e}")

    def _create_employees_page(self):
        """Создать страницу управления сотрудниками."""
        self.employees_page = EmployeesPage(
            employee_service=self.employee_service
        )

        self.ui.stackedWidget.addWidget(self.employees_page)
        self.employees_page_index = self.ui.stackedWidget.indexOf(self.employees_page)

        logger.debug("Страница сотрудников добавлена с индексом: %d", self.employees_page_index)


__all__ = ["MainWindow"]