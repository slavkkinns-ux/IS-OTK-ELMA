"""Главное окно приложения ИС ОТК."""
import sys
from datetime import datetime, date

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QMainWindow, QButtonGroup, QHeaderView, QTableWidgetItem,
    QMessageBox, QDialog, QDateEdit, QLabel, QPushButton,
    QHBoxLayout, QLineEdit, QGroupBox, QFormLayout, QWidget,
)

from ui.main_window_ui import Ui_MainWindow
from session import Session
from dialogs import (
    OrderDialog, ViewOrderDialog,
    ClientDialog, ClientEditDialog, ClientViewDialog,
)
from db import client_repo, order_repo, report_repo


# =============================================================================
# Утилиты
# =============================================================================

def format_date(value) -> str:
    """Безопасно форматирует дату/дата-время в строку ДД.ММ.ГГГГ."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return str(value)


class SortableTableWidgetItem(QTableWidgetItem):
    """Ячейка таблицы с правильной сортировкой чисел и дат."""

    def __init__(self, text: str, sort_value=None):
        super().__init__(text)
        self._sort_value = sort_value if sort_value is not None else text

    def __lt__(self, other):
        try:
            return float(self._sort_value) < float(other._sort_value)
        except (ValueError, TypeError):
            return str(self._sort_value) < str(other._sort_value)


# =============================================================================
# Главное окно
# =============================================================================

class MainWindow(QMainWindow):
    """Главное окно приложения."""

    def __init__(self, app):
        super().__init__()
        self.app = app

        from db import connect
        try:
            connect()
        except Exception as e:
            QMessageBox.critical(None, "Ошибка", f"Не удалось подключиться к БД:\n{e}")
            sys.exit(1)

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

    def closeEvent(self, event):
        from db import close
        close()
        event.accept()

    def show_page(self, page):
        self.ui.stackedWidget.setCurrentWidget(page)

    def logout(self):
        Session.clear()
        self.close()

    # =========================================================================
    # НАВИГАЦИЯ И ОБЩЕЕ
    # =========================================================================

    def _setup_sidebar(self):
        """Настройка бокового меню и стилей кнопок."""
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
            self.ui.btnResearch, self.ui.btnReports,
        ]
        for btn in nav_buttons:
            self.nav_group.addButton(btn)
            btn.setCheckable(True)
        self.ui.btnHome.setChecked(True)
        self.nav_group.buttonClicked.connect(self._on_nav_clicked)
        self.ui.btnExit.clicked.connect(self.logout)

    def _apply_role_permissions(self):
        """Применение прав доступа в зависимости от роли пользователя."""
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
        # Последние заказы
        h = self.ui.tableRecentOrders.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # Все заказы
        h = self.ui.tableOrders.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableOrders.setColumnWidth(1, 220)
        self.ui.tableOrders.setColumnWidth(3, 200)
        self.ui.tableOrders.setWordWrap(True)

        # Клиенты
        h = self.ui.tableClients.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.ui.tableClients.setColumnWidth(1, 220)
        self.ui.tableClients.setColumnWidth(3, 200)
        self.ui.tableClients.setWordWrap(True)

        # Очередь исследований
        h = self.ui.tableResearchQueue.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)
        self.ui.tableResearchQueue.setColumnWidth(2, 150)
        self.ui.tableResearchQueue.setColumnWidth(3, 150)
        self.ui.tableResearchQueue.setWordWrap(True)

        # Исследования отчёта
        h = self.ui.tableReportResearch.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        self.ui.tableReportResearch.setColumnWidth(0, 140)
        self.ui.tableReportResearch.setColumnWidth(1, 140)
        self.ui.tableReportResearch.setColumnWidth(2, 140)
        self.ui.tableReportResearch.setWordWrap(True)

        # Последние отчёты
        h = self.ui.tableRecentReports.horizontalHeader()
        h.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        h.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)

        # Скрыть вертикальные заголовки и включить сортировку
        for table in [
            self.ui.tableRecentOrders, self.ui.tableOrders, self.ui.tableClients,
            self.ui.tableResearchQueue, self.ui.tableReportResearch,
            self.ui.tableRecentReports,
        ]:
            table.setSortingEnabled(True)
            table.verticalHeader().setVisible(False)

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

    # =========================================================================
    # HOME — Главная страница
    # =========================================================================

    def _setup_home_tab(self):
        self.ui.btnAllOrders.clicked.connect(self._go_to_orders)
        self._load_home_stats()
        self._load_recent_orders()

    def _load_home_stats(self):
        stats = order_repo.get_home_stats()
        if not stats:
            return
        self.ui.lblOrderValue.setText(str(stats['total_orders']))
        self.ui.lblActiveOrdersValue.setText(str(stats['active_orders']))
        self.ui.lblClientsValue.setText(str(stats['total_clients']))
        self.ui.lblPendingChecksValue.setText(str(stats['pending_checks']))

    def _load_recent_orders(self):
        orders = order_repo.get_recent_orders(limit=5)
        self._populate_recent_orders_table(orders)

    def _populate_recent_orders_table(self, orders):
        self.ui.tableRecentOrders.setSortingEnabled(False)
        self.ui.tableRecentOrders.setRowCount(0)
        if not orders:
            self.ui.tableRecentOrders.setSortingEnabled(True)
            return
        self.ui.tableRecentOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            item_vessel = SortableTableWidgetItem(str(order['vessel_code']))
            self.ui.tableRecentOrders.setItem(row_idx, 0, item_vessel)

            item_client = SortableTableWidgetItem(order['client_name'] or '')
            self.ui.tableRecentOrders.setItem(row_idx, 1, item_client)

            item_date = SortableTableWidgetItem(
                format_date(order['order_date']),
                sort_value=order['order_date']
            )
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 2, item_date)

            item_status = SortableTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 3, item_status)
        self.ui.tableRecentOrders.setSortingEnabled(True)

    def _go_to_orders(self):
        self.ui.btnOrders.setChecked(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageOrders)

    # =========================================================================
    # ORDERS — Заказы
    # =========================================================================

    def _setup_orders_tab(self):
        self.ui.btnAddOrder.clicked.connect(self._add_order)
        self.ui.btnEditOrder.clicked.connect(self._edit_order)
        self.ui.btnViewOrder.clicked.connect(self._view_order)
        self.ui.btnRefreshOrder.clicked.connect(self._load_orders_stats)

        self.ui.btnSearchOrders.clicked.connect(self._search_orders)
        self.ui.btnResetOrderFilters.clicked.connect(self._reset_filters)
        self.ui.editOrderSearch.returnPressed.connect(self._search_orders)
        self.ui.comboOrderStatus.currentIndexChanged.connect(self._search_orders)

        self._add_orders_date_filter()

        self._load_orders_stats()
        self._load_orders_table()

    def _load_orders_stats(self):
        stats = order_repo.get_orders_stats()
        if not stats:
            return
        self.ui.lblTotalOrdersValue.setText(str(stats['total']))
        self.ui.lblOrdersInProgressValue.setText(str(stats['in_progress']))
        self.ui.lblOrdersPendingValue.setText(str(stats['pending']))
        self.ui.lblOrdersCompletedValue.setText(str(stats['completed']))

    def _load_orders_table(self):
        orders = order_repo.get_all_orders()
        self._populate_orders_table(orders)

    def _populate_orders_table(self, orders):
        self.ui.tableOrders.setSortingEnabled(False)
        self.ui.tableOrders.setRowCount(0)
        if not orders:
            self.ui.tableOrders.setSortingEnabled(True)
            return
        self.ui.tableOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            item_vessel = SortableTableWidgetItem(
                str(order['vessel_code']),
                sort_value=order['order_id']
            )
            item_vessel.setData(Qt.ItemDataRole.UserRole, order['order_id'])
            self.ui.tableOrders.setItem(row_idx, 0, item_vessel)

            item_client = QTableWidgetItem(order.get('client_name') or '')
            self.ui.tableOrders.setItem(row_idx, 1, item_client)

            item_date = SortableTableWidgetItem(
                format_date(order.get('order_date')),
                sort_value=order.get('order_date')
            )
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 2, item_date)

            item_employee = QTableWidgetItem(order.get('employee_name') or '')
            self.ui.tableOrders.setItem(row_idx, 3, item_employee)

            item_status = QTableWidgetItem(order.get('status') or '')
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 4, item_status)

            item_completion = QTableWidgetItem('-')
            item_completion.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 5, item_completion)

            item_actions = QTableWidgetItem('')
            item_actions.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 6, item_actions)
        self.ui.tableOrders.setSortingEnabled(True)

    def _add_orders_date_filter(self):
        """Добавляем фильтр по диапазону дат в строку фильтров заказов."""
        filters_layout = self.ui.filtersFrameOrders.layout()
        if not filters_layout:
            return

        filters_layout.addWidget(QLabel("С:"))
        self.dateFrom = QDateEdit()
        self.dateFrom.setCalendarPopup(True)
        self.dateFrom.setDisplayFormat("dd.MM.yyyy")
        self.dateFrom.setDate(QDate.currentDate().addMonths(-1))
        self.dateFrom.dateChanged.connect(self._search_orders)
        filters_layout.addWidget(self.dateFrom)

        filters_layout.addWidget(QLabel("По:"))
        self.dateTo = QDateEdit()
        self.dateTo.setCalendarPopup(True)
        self.dateTo.setDisplayFormat("dd.MM.yyyy")
        self.dateTo.setDate(QDate.currentDate())
        self.dateTo.dateChanged.connect(self._search_orders)
        filters_layout.addWidget(self.dateTo)

    def _search_orders(self):
        """Поиск заказов: текст + статус + диапазон дат."""
        query = self.ui.editOrderSearch.text().strip().lower()
        status = self.ui.comboOrderStatus.currentText()

        orders = order_repo.get_all_orders()
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
            if hasattr(self, 'dateFrom') and hasattr(self, 'dateTo'):
                order_date = o.get('order_date')
                if order_date:
                    if isinstance(order_date, datetime):
                        order_date = order_date.date()
                    match_date = (
                        order_date >= self.dateFrom.date().toPyDate()
                        and order_date <= self.dateTo.date().toPyDate()
                    )

            if match_text and match_status and match_date:
                filtered.append(o)

        self._populate_orders_table(filtered)

    def _reset_filters(self):
        self.ui.editOrderSearch.clear()
        self.ui.comboOrderStatus.setCurrentIndex(0)
        if hasattr(self, 'dateFrom'):
            self.dateFrom.setDate(QDate.currentDate().addMonths(-1))
            self.dateTo.setDate(QDate.currentDate())
        self._load_orders_table()

    def _add_order(self):
        dlg = OrderDialog(self, order_id=None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_orders_table()
            self._load_orders_stats()
            self._load_home_stats()
            self._load_recent_orders()
            self._load_reports_combo()

    def _edit_order(self):
        row = self.ui.tableOrders.currentRow()
        if row < 0:
            QMessageBox.information(self, "Редактирование", "Выберите заказ в таблице.")
            return
        order_id = self._get_selected_order_id(row)
        if not order_id:
            return
        dlg = OrderDialog(self, order_id=order_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_orders_table()
            self._load_orders_stats()
            self._load_recent_orders()
            self._load_reports_combo()

    def _view_order(self):
        row = self.ui.tableOrders.currentRow()
        if row < 0:
            QMessageBox.information(self, "Просмотр", "Выберите заказ в таблице.")
            return
        order_id = self._get_selected_order_id(row)
        if not order_id:
            return
        dlg = ViewOrderDialog(self, order_id=order_id)
        dlg.exec()

    def _get_selected_order_id(self, row: int) -> int | None:
        item = self.ui.tableOrders.item(row, 0)
        if item is None:
            return None
        oid = item.data(Qt.ItemDataRole.UserRole)
        if oid:
            return int(oid)
        vessel = item.text()
        orders = order_repo.get_all_orders()
        for o in orders:
            if o.get('vessel_code') == vessel:
                return o['order_id']
        return None

    # =========================================================================
    # CLIENTS — Клиенты
    # =========================================================================

    def _setup_clients_tab(self):
        self.ui.brnRefreshClients.clicked.connect(self._refresh_clients_page)
        self.ui.btnAddClient.clicked.connect(self._add_client)
        self.ui.btnEditClient.clicked.connect(self._edit_client)
        self.ui.btnViewClient.clicked.connect(self._view_client)

        self.ui.btnSearchClients.clicked.connect(self._search_clients)
        self.ui.btnResetClientFilters.clicked.connect(self._reset_client_filters)
        self.ui.editClientsSearch.returnPressed.connect(self._search_clients)

        self._load_clients_to_table()
        self._load_clients_stats()

    def _load_clients_stats(self):
        stats = client_repo.get_clients_stats()
        if not stats:
            return
        self.ui.lblcardTotalClientsValue.setText(str(stats['total_clients']))
        self.ui.lblcardActiveClientsValue.setText(str(stats['active_clients']))
        self.ui.lblcardClientsWithOrdersValue.setText(str(stats['clients_with_orders']))

    def _load_clients_to_table(self):
        clients = client_repo.get_all_clients()
        orders_count = client_repo.get_clients_orders_count()
        self._populate_clients_table(clients, orders_count)

    def _populate_clients_table(self, clients, orders_count=None):
        if orders_count is None:
            orders_count = client_repo.get_clients_orders_count()

        self.ui.tableClients.setSortingEnabled(False)
        self.ui.tableClients.setRowCount(0)
        if not clients:
            self.ui.tableClients.setSortingEnabled(True)
            return
        self.ui.tableClients.setRowCount(len(clients))
        for row_idx, c in enumerate(clients):
            item_id = SortableTableWidgetItem(
                str(c['client_id']),
                sort_value=c['client_id']
            )
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 0, item_id)

            self.ui.tableClients.setItem(
                row_idx, 1, QTableWidgetItem(c.get('name', '')))

            item_details = QTableWidgetItem(c.get('details', ''))
            item_details.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 2, item_details)

            self.ui.tableClients.setItem(
                row_idx, 3, QTableWidgetItem(c.get('contact_person', '')))

            count = orders_count.get(c['client_id'], 0)
            item_orders = SortableTableWidgetItem(
                str(count),
                sort_value=count
            )
            item_orders.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 4, item_orders)
        self.ui.tableClients.setSortingEnabled(True)

    def _search_clients(self):
        query = self.ui.editClientsSearch.text().strip().lower()
        if not query:
            self._load_clients_to_table()
            return
        clients = client_repo.get_all_clients()
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
        self.ui.editClientsSearch.clear()
        self._load_clients_to_table()

    def _add_client(self):
        dlg = ClientDialog(self, initial_type="ЮЛ")
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_clients_page()
            self._load_home_stats()

    def _edit_client(self):
        row = self.ui.tableClients.currentRow()
        if row < 0:
            QMessageBox.information(self, "Редактирование", "Выберите клиента в таблице.")
            return
        client_id = int(self.ui.tableClients.item(row, 0).text())
        dlg = ClientEditDialog(self, client_id)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._refresh_clients_page()

    def _view_client(self):
        row = self.ui.tableClients.currentRow()
        if row < 0:
            QMessageBox.information(self, "Просмотр", "Выберите клиента в таблице.")
            return
        client_id = int(self.ui.tableClients.item(row, 0).text())
        dlg = ClientViewDialog(self, client_id)
        dlg.exec()

    def _refresh_clients_page(self):
        self._load_clients_to_table()
        self._load_clients_stats()

    # =========================================================================
    # RESEARCH — Исследования
    # =========================================================================

    
    def _setup_research_tab(self):
        """Настройка вкладки исследований."""
        # Кнопки действий
        self.ui.btnSaveResearchResult.clicked.connect(self._save_research)
        self.ui.btnClearResearchResult.clicked.connect(self._clear_research)
        self.ui.btnViewResearchResult.clicked.connect(self._view_research)

        # Поиск и фильтр
        self.ui.editResearchSearch.textChanged.connect(self._search_research)
        self.ui.comboResearchFilter.currentIndexChanged.connect(self._search_research)

        # Клик по строке таблицы
        self.ui.tableResearchQueue.clicked.connect(self._on_research_row_selected)

        # Инициализация текущего выбранного исследования
        self._current_order_service_id = None

        # Загрузка данных
        self._load_research_queue()
        self._load_employees_combo()

        # Очистка правой панели при старте
        self._clear_research_details()


    def _load_employees_combo(self):
        """Загрузить список активных сотрудников в comboResearchEmployee."""
        employees = report_repo.get_all_employees()
        self.ui.comboResearchEmployee.blockSignals(True)
        self.ui.comboResearchEmployee.clear()
        for emp in employees:
            self.ui.comboResearchEmployee.addItem(emp['full_name'], emp['employee_id'])
        self.ui.comboResearchEmployee.blockSignals(False)


    def _on_research_row_selected(self, index):
        """Обработка клика по строке в таблице исследований."""
        row = index.row()
        if row < 0:
            return

        # Получаем данные из строки
        order_id = self.ui.tableResearchQueue.item(row, 0).text()
        vessel_code = self.ui.tableResearchQueue.item(row, 1).text()
        service_name = self.ui.tableResearchQueue.item(row, 2).text()
        client_name = self.ui.tableResearchQueue.item(row, 3).text()

        # Показываем в правой панели
        self.ui.lblResearchOrderValue.setText(order_id)
        self.ui.lblResearchVesselValue.setText(vessel_code)
        self.ui.lblResearchClientValue.setText(client_name)
        self.ui.lblResearchServiceValue.setText(service_name)

        # Получаем order_service_id из UserRole
        item = self.ui.tableResearchQueue.item(row, 0)
        order_service_id = item.data(Qt.ItemDataRole.UserRole)
        if order_service_id:
            self._current_order_service_id = order_service_id
            # Загружаем существующий результат, если есть
            self._load_existing_research_result(order_service_id)


    def _load_existing_research_result(self, order_service_id: int):
        """Загрузить существующий результат исследования в поля."""
        result = report_repo.get_research_result(order_service_id)
        if result:
            self.ui.editResearchResultValue.setText(result.get('result_value', '') or '')
            self.ui.textResearchConclusion.setPlainText(result.get('conclusion', '') or '')
            if result.get('result_date'):
                from PyQt6.QtCore import QDate
                result_date = result['result_date']
                if hasattr(result_date, 'toPyDate'):
                    self.ui.dateResearchResult.setDate(result_date)
                else:
                    self.ui.dateResearchResult.setDate(QDate.fromString(str(result_date), 'yyyy-MM-dd'))
            # Устанавливаем сотрудника, если он есть
            if result.get('employee_id'):
                for i in range(self.ui.comboResearchEmployee.count()):
                    if self.ui.comboResearchEmployee.itemData(i) == result['employee_id']:
                        self.ui.comboResearchEmployee.setCurrentIndex(i)
                        break
        else:
            self._clear_research_details()


    def _clear_research_details(self):
        """Очистить правую панель."""
        self.ui.lblResearchOrderValue.setText('')
        self.ui.lblResearchVesselValue.setText('')
        self.ui.lblResearchClientValue.setText('')
        self.ui.lblResearchServiceValue.setText('')
        self.ui.editResearchResultValue.clear()
        self.ui.textResearchConclusion.clear()
        from PyQt6.QtCore import QDate
        self.ui.dateResearchResult.setDate(QDate.currentDate())
        self._current_order_service_id = None


    def _save_research(self):
        """Сохранить результат исследования."""
        if not hasattr(self, '_current_order_service_id') or not self._current_order_service_id:
            QMessageBox.warning(self, "Ошибка", "Выберите исследование из списка.")
            return

        result_value = self.ui.editResearchResultValue.text().strip()
        conclusion = self.ui.textResearchConclusion.toPlainText().strip()
        result_date = self.ui.dateResearchResult.date().toPyDate()
        employee_id = self.ui.comboResearchEmployee.currentData()

        if not result_value:
            QMessageBox.warning(self, "Ошибка", "Введите результат исследования.")
            return

        try:
            report_repo.save_research_result(
                order_service_id=self._current_order_service_id,
                employee_id=employee_id,
                result_value=result_value,
                conclusion=conclusion,
                result_date=result_date
            )
            QMessageBox.information(self, "Готово", "Результат исследования сохранён.")
            # Обновляем таблицу
            self._load_research_queue()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить результат:\n{e}")


    def _clear_research(self):
        """Очистить поля ввода результата."""
        self.ui.editResearchResultValue.clear()
        self.ui.textResearchConclusion.clear()
        from PyQt6.QtCore import QDate
        self.ui.dateResearchResult.setDate(QDate.currentDate())


    def _view_research(self):
        """Просмотреть результат исследования."""
        if not hasattr(self, '_current_order_service_id') or not self._current_order_service_id:
            QMessageBox.warning(self, "Просмотр", "Выберите исследование из списка.")
            return

        # Собираем информацию об исследовании из текущей строки
        row = self.ui.tableResearchQueue.currentRow()
        research_info = {
            'order_id': self.ui.tableResearchQueue.item(row, 0).text(),
            'vessel_code': self.ui.tableResearchQueue.item(row, 1).text(),
            'service_name': self.ui.tableResearchQueue.item(row, 2).text(),
            'client_name': self.ui.tableResearchQueue.item(row, 3).text(),
        }

        from dialogs.research_result_dialog import ResearchResultDialog
        dlg = ResearchResultDialog(
            self,
            order_service_id=self._current_order_service_id,
            research_info=research_info,
        )
        dlg.exec()


    def _load_research_queue(self):
        """Загрузка очереди исследований."""
        research = report_repo.get_research_queue()
        self._populate_research_table(research)


    def _populate_research_table(self, research):
        """Заполнить таблицу исследований."""
        self.ui.tableResearchQueue.setSortingEnabled(False)
        self.ui.tableResearchQueue.setRowCount(0)
        if not research:
            self.ui.tableResearchQueue.setSortingEnabled(True)
            return

        self.ui.tableResearchQueue.setRowCount(len(research))
        for row_idx, item in enumerate(research):
            # Номер заказа — сортируем как число
            item_order = SortableTableWidgetItem(
                str(item['order_id']),
                sort_value=item['order_id']
            )
            item_order.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            # Сохраняем order_service_id в UserRole для последующего использования
            item_order.setData(Qt.ItemDataRole.UserRole, item['order_service_id'])
            self.ui.tableResearchQueue.setItem(row_idx, 0, item_order)

            # Код сосуда
            item_vessel = SortableTableWidgetItem(str(item['vessel_code']))
            self.ui.tableResearchQueue.setItem(row_idx, 1, item_vessel)

            # Услуга
            item_service = SortableTableWidgetItem(item['service_name'])
            self.ui.tableResearchQueue.setItem(row_idx, 2, item_service)

            # Клиент
            item_client = SortableTableWidgetItem(item['client_name'] or '')
            self.ui.tableResearchQueue.setItem(row_idx, 3, item_client)

            # Результат
            result_text = item['result_value'] if item['result_value'] else 'Не выполнено'
            item_result = SortableTableWidgetItem(result_text)
            item_result.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableResearchQueue.setItem(row_idx, 4, item_result)

        self.ui.tableResearchQueue.setSortingEnabled(True)
        self.ui.tableResearchQueue.resizeRowsToContents()


    def _search_research(self):
        """Фильтрация очереди исследований по тексту и наличию результата."""
        query = self.ui.editResearchSearch.text().strip().lower()
        filter_mode = self.ui.comboResearchFilter.currentIndex()  # 0=все, 1=без, 2=с

        research = report_repo.get_research_queue()
        filtered = []
        for item in research:
            # Текстовый фильтр
            match_text = True
            if query:
                search_str = (
                    f"{item.get('vessel_code', '')} "
                    f"{item.get('service_name', '')} "
                    f"{item.get('client_name', '')} "
                    f"{item.get('order_id', '')}"
                ).lower()
                match_text = query in search_str

            # Фильтр по результату
            match_result = True
            if filter_mode == 1:  # Без результата
                match_result = not bool(item.get('result_value'))
            elif filter_mode == 2:  # С результатом
                match_result = bool(item.get('result_value'))

            if match_text and match_result:
                filtered.append(item)

        self._populate_research_table(filtered)

    # =========================================================================
    # REPORTS — Отчёты
    # =========================================================================

    def _setup_reports_tab(self):
        self.ui.btnCreateReport.clicked.connect(self._create_report)
        self.ui.btnOpenReport.clicked.connect(self._open_report)
        self.ui.btnPrintReport.clicked.connect(self._print_report)
        self.ui.comboreportsOrder.currentIndexChanged.connect(self._on_report_order_changed)

        self._load_reports_combo()
        self._load_recent_reports()

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
            self.ui.tableReportResearch.setItem(
                row_idx, 0, QTableWidgetItem(r['service_name']))
            self.ui.tableReportResearch.setItem(
                row_idx, 1, QTableWidgetItem(r['result_value'] or 'Не выполнено'))
            self.ui.tableReportResearch.setItem(
                row_idx, 2, QTableWidgetItem(r['conclusion'] or '-'))
        self.ui.tableReportResearch.resizeRowsToContents()

    def _load_recent_reports(self):
        rows = report_repo.get_recent_reports()
        self._populate_recent_reports_table(rows)

    def _populate_recent_reports_table(self, rows):
        self.ui.tableRecentReports.setSortingEnabled(False)
        self.ui.tableRecentReports.setRowCount(0)
        if not rows:
            self.ui.tableRecentReports.setSortingEnabled(True)
            return
        self.ui.tableRecentReports.setRowCount(len(rows))
        for row_idx, r in enumerate(rows):
            item_report_id = SortableTableWidgetItem(
                f"ОТЧ-{r['report_id']:04d}",
                sort_value=r['report_id']
            )
            self.ui.tableRecentReports.setItem(row_idx, 0, item_report_id)

            item_vessel = SortableTableWidgetItem(r['vessel_code'])
            self.ui.tableRecentReports.setItem(row_idx, 1, item_vessel)

            item_date = SortableTableWidgetItem(
                format_date(r['report_date']),
                sort_value=r['report_date']
            )
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentReports.setItem(row_idx, 2, item_date)

            item_employee = SortableTableWidgetItem(r['employee_name'])
            self.ui.tableRecentReports.setItem(row_idx, 3, item_employee)
        self.ui.tableRecentReports.setSortingEnabled(True)

    def _create_report(self):
        pass  # TODO: реализовать формирование отчёта

    def _open_report(self):
        pass  # TODO: реализовать открытие PDF

    def _print_report(self):
        pass  # TODO: реализовать печать