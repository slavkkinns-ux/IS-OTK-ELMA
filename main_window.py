import sys
from PyQt6.QtWidgets import QMainWindow, QButtonGroup, QHeaderView, QTableWidgetItem, QMessageBox, QDialog
from PyQt6.QtCore import Qt
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.main_window_ui import Ui_MainWindow
from session import Session
from dialogs import OrderDialog, ViewOrderDialog, ClientDialog, ClientEditDialog, ClientViewDialog
from db import client_repo, order_repo, report_repo
from datetime import datetime, date


def format_date(value) -> str:
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return str(value)


class MainWindow(QMainWindow):
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

    # ==================== HOME ====================
    def _setup_home_tab(self):
        self.ui.btnAllOrders.clicked.connect(self._go_to_orders)
        self._load_home_stats()
        self._load_recent_orders()

    # ==================== ORDERS ====================
    def _setup_orders_tab(self):
        self.ui.btnAddOrder.clicked.connect(self._add_order)
        self.ui.btnEditOrder.clicked.connect(self._edit_order)
        self.ui.btnViewOrder.clicked.connect(self._view_order)
        self.ui.btnRefreshOrder.clicked.connect(self._load_orders_stats)
        self.ui.btnSearchOrders.clicked.connect(self._search_orders)
        self.ui.btnResetOrderFilters.clicked.connect(self._reset_filters)
        self.ui.editOrderSearch.returnPressed.connect(self._search_orders)
        self.ui.comboOrderStatus.currentIndexChanged.connect(self._search_orders)
        self._load_orders_stats()
        self._load_orders_table()

    # ==================== CLIENTS ====================
    def _setup_clients_tab(self):
        """Настройка вкладки клиентов."""
        self.ui.brnRefreshClients.clicked.connect(self._refresh_clients_page)
        self.ui.btnAddClient.clicked.connect(self._add_client)
        self.ui.btnEditClient.clicked.connect(self._edit_client)
        self.ui.btnViewClient.clicked.connect(self._view_client)
        self.ui.btnSearchClients.clicked.connect(self._search_clients)
        self.ui.btnResetClientFilters.clicked.connect(self._reset_client_filters)
        self.ui.editClientsSearch.returnPressed.connect(self._search_clients)
        self._load_clients_to_table()
        self._load_clients_stats()

    def _populate_clients_table(self, clients):
        """Заполнить таблицу клиентов."""
        orders_count = client_repo.get_clients_orders_count()
        self.ui.tableClients.setRowCount(0)
        if not clients:
            return
        self.ui.tableClients.setRowCount(len(clients))
        for row_idx, c in enumerate(clients):
            item_id = QTableWidgetItem(str(c['client_id']))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 0, item_id)

            self.ui.tableClients.setItem(row_idx, 1, QTableWidgetItem(c.get('name', '')))

            item_details = QTableWidgetItem(c.get('details', ''))
            item_details.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 2, item_details)

            self.ui.tableClients.setItem(row_idx, 3, QTableWidgetItem(c.get('contact_person', '')))

            item_orders = QTableWidgetItem(str(orders_count.get(c['client_id'], 0)))
            item_orders.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 4, item_orders)

    def _load_clients_to_table(self):
        clients = client_repo.get_all_clients()
        self._populate_clients_table(clients)

    def _search_clients(self):
        query = self.ui.editClientsSearch.text().strip().lower()
        if not query:
            self._load_clients_to_table()
            return
        clients = client_repo.get_all_clients()
        filtered = []
        for c in clients:
            search_str = f"{c.get('name', '')} {c.get('details', '')} {c.get('contact_person', '')}".lower()
            if query in search_str:
                filtered.append(c)
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

    # ==================== RESEARCH ====================
    def _setup_research_tab(self):
        self.ui.btnSaveResearchResult.clicked.connect(self._save_research)
        self.ui.btnClearResearchResult.clicked.connect(self._clear_research)
        self.ui.btnViewResearchResult.clicked.connect(self._view_research)
        self._load_research_queue()

    # ==================== REPORTS ====================
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

    def _add_order(self):
        dlg = OrderDialog(self, order_id=None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_orders_table()
            self._load_orders_stats()
            self._load_home_stats()
            self._load_recent_orders()
            self._load_reports_combo()

    def _search_orders(self):
        query = self.ui.editOrderSearch.text().strip().lower()
        status = self.ui.comboOrderStatus.currentText()
        orders = order_repo.get_all_orders()
        filtered = []
        for o in orders:
            match_text = True
            if query:
                search_str = f"{o.get('vessel_code', '')} {o.get('client_name', '')} {o.get('order_id', '')}".lower()
                match_text = query in search_str
            match_status = True
            if status and status != "Все статусы":
                match_status = (o.get('status') == status)
            if match_text and match_status:
                filtered.append(o)
        self._populate_orders_table(filtered)

    def _reset_filters(self):
        self.ui.editOrderSearch.clear()
        self.ui.comboOrderStatus.setCurrentIndex(0)
        self._load_orders_table()

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

    def _save_research(self):
        pass

    def _create_report(self):
        pass

    def _clear_research(self):
        pass

    def _view_research(self):
        pass

    def _open_report(self):
        pass

    def _print_report(self):
        pass

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
            return
        self.ui.tableRecentOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            self.ui.tableRecentOrders.setItem(row_idx, 0, item_vessel)
            item_client = QTableWidgetItem(order['client_name'] or '')
            self.ui.tableRecentOrders.setItem(row_idx, 1, item_client)
            item_date = QTableWidgetItem(format_date(order['order_date']))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 2, item_date)
            item_status = QTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentOrders.setItem(row_idx, 3, item_status)

    def _load_orders_table(self):
        orders = order_repo.get_all_orders()
        self._populate_orders_table(orders)

    def _load_research_queue(self):
        research = report_repo.get_research_queue()
        self.ui.tableResearchQueue.setRowCount(0)
        if not research:
            return
        self.ui.tableResearchQueue.setRowCount(len(research))
        for row_idx, item in enumerate(research):
            item_order = QTableWidgetItem(str(item['order_id']))
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
            item_date = QTableWidgetItem(format_date(r['report_date']))
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableRecentReports.setItem(row_idx, 2, item_date)
            self.ui.tableRecentReports.setItem(row_idx, 3, QTableWidgetItem(r['employee_name']))

    def _populate_orders_table(self, orders):
        self.ui.tableOrders.setRowCount(0)
        if not orders:
            return
        self.ui.tableOrders.setRowCount(len(orders))
        for row_idx, order in enumerate(orders):
            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            item_vessel.setData(Qt.ItemDataRole.UserRole, order['order_id'])
            self.ui.tableOrders.setItem(row_idx, 0, item_vessel)
            item_client = QTableWidgetItem(order.get('client_name') or '')
            self.ui.tableOrders.setItem(row_idx, 1, item_client)
            item_date = QTableWidgetItem(format_date(order.get('order_date')))
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