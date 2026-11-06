from PyQt6.QtWidgets import QMainWindow, QButtonGroup, QHeaderView, QTableWidgetItem, QMessageBox, QDialog
from PyQt6.QtCore import Qt
from PyQt6 import QtCore, QtGui, QtWidgets
from ui.main_window_ui import Ui_MainWindow
from session import Session, Role
from db import Database

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

        self._setup_sidebar()
        self._apply_role_permissions()
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
        # ==========================================
        # 1. Таблица последних заказов (4 колонки)
        # ==========================================
        header_recent = self.ui.tableRecentOrders.horizontalHeader()
        header_recent.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_recent.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_recent.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_recent.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)

        # ==========================================
        # 2. Таблица всех заказов (7 колонок)
        # ==========================================
        header_orders = self.ui.tableOrders.horizontalHeader()
        header_orders.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_orders.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_orders.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header_orders.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)

        # ==========================================
        # 3. Таблица клиентов (5 колонок)
        # ==========================================
        header_clients = self.ui.tableClients.horizontalHeader()
        header_clients.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header_clients.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header_clients.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header_clients.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        header_clients.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)

        # ==========================================
        # 4. Таблица очереди исследований (5 колонок)
        # ==========================================
        header_research = self.ui.tableResearchQueue.horizontalHeader()
        
        # Короткие колонки - по содержимому
        header_research.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Заказ
        header_research.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Код сосуда
        header_research.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Результат
        
        # Длинные колонки - растягиваются, но с минимальной шириной 150px
        header_research.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Исследование
        header_research.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Клиент
        
        # Устанавливаем начальную ширину 150px для длинных колонок
        self.ui.tableResearchQueue.setColumnWidth(2, 150)  # Исследование
        self.ui.tableResearchQueue.setColumnWidth(3, 150)  # Клиент
        
        # Включаем перенос текста
        self.ui.tableResearchQueue.setWordWrap(True)

        # ==========================================
        # 5. Таблица исследований в отчете (3 колонки)
        # ==========================================
        header_report = self.ui.tableReportResearch.horizontalHeader()
        header_report.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)           # Исследование
        header_report.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Результат
        header_report.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Заключение

        # ==========================================
        # 6. Таблица последних отчетов (4 колонки)
        # ==========================================
        header_recent_rep = self.ui.tableRecentReports.horizontalHeader()
        header_recent_rep.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # Номер отчёта
        header_recent_rep.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Номер заказа
        header_recent_rep.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Дата
        header_recent_rep.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)           # Сотрудник

        # ==========================================
        # 7. Общие настройки для ВСЕХ таблиц
        # ==========================================
        for table in [
            self.ui.tableRecentOrders, 
            self.ui.tableOrders, 
            self.ui.tableClients,
            self.ui.tableResearchQueue, 
            self.ui.tableReportResearch, 
            self.ui.tableRecentReports
        ]:
            # Скрываем вертикальный заголовок (номера строк)
            table.verticalHeader().setVisible(False)
            
            # ВАЖНО: Мы УБРАЛИ отсюда table.horizontalHeader().setStretchLastSection(True), 
            # так как это часто конфликтует с явным заданием ResizeToContents/Stretch 
            # и является главной причиной появления "...".

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
        self.ui.btnRefreshOrder.clicked.connect(self._load_orders_stats)
        self._load_orders_stats()
        self._load_orders_table()

    def _setup_clients_tab(self):
        self.ui.brnRefreshClients.clicked.connect(self._refresh_clients_page)
        self._load_clients_to_table()
        self._load_clients_stats()

    def _load_clients_to_table(self):
        db = Database()
        clients = db.get_all_clients()
        
        self.ui.tableClients.setRowCount(0)
        
        if not clients:
            return

        self.ui.tableClients.setRowCount(len(clients))
        
        for row_idx, client in enumerate(clients):
            item_id = QtWidgets.QTableWidgetItem(str(client['client_id']))
            item_id.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 0, item_id)
            
            item_name = QtWidgets.QTableWidgetItem(client['name'])
            self.ui.tableClients.setItem(row_idx, 1, item_name)
            
            item_details = QtWidgets.QTableWidgetItem(client['details'])
            item_details.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 2, item_details)
            
            item_contact = QtWidgets.QTableWidgetItem(client['contact_person'])
            self.ui.tableClients.setItem(row_idx, 3, item_contact)
            
            item_orders = QtWidgets.QTableWidgetItem("0")
            item_orders.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            self.ui.tableClients.setItem(row_idx, 4, item_orders)

    def _setup_research_tab(self):
        self.ui.btnSaveResearchResult.clicked.connect(self._save_research)
        self.ui.btnClearResearchResult.clicked.connect(self._clear_research)
        self.ui.btnViewResearchResult.clicked.connect(self._view_research)
        self._load_research_queue()

    def _setup_reports_tab(self):
        self.ui.btnCreateReport.clicked.connect(self._create_report)

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

    def _go_to_orders(self):
        self.ui.btnOrders.setChecked(True)
        self.ui.stackedWidget.setCurrentWidget(self.ui.pageOrders)

    def _add_order(self):
        pass

    def _search_orders(self):
        pass

    def _edit_order(self):
        pass

    def _add_client(self):
        pass

    def _save_research(self):
        pass

    def _create_report(self):
        pass

    def _view_order(self):
        pass

    def _clear_research(self):
        pass

    def _view_research(self):
        pass

    def _refresh_clients_page(self):
        self._load_clients_to_table()
        self._load_clients_stats()
    
    def _load_home_stats(self):
        db = Database()
        stats = db.get_home_stats()
        if not stats:
            return
        self.ui.lblOrderValue.setText(str(stats['total_orders']))
        self.ui.lblActiveOrdersValue.setText(str(stats['active_orders']))
        self.ui.lblClientsValue.setText(str(stats['total_clients']))
        self.ui.lblPendingChecksValue.setText(str(stats['pending_checks']))

    def _load_orders_stats(self):
        db = Database()
        stats = db.get_orders_stats()
        if not stats:
            return
        self.ui.lblTotalOrdersValue.setText(str(stats['total']))
        self.ui.lblOrdersInProgressValue.setText(str(stats['in_progress']))
        self.ui.lblOrdersPendingValue.setText(str(stats['pending']))
        self.ui.lblOrdersCompletedValue.setText(str(stats['completed']))

    def _load_clients_stats(self):
        db = Database()
        stats = db.get_clients_stats()
        if not stats:
            return
        self.ui.lblcardTotalClientsValue.setText(str(stats['total_clients']))
        self.ui.lblcardActiveClientsValue.setText(str(stats['active_clients']))
        self.ui.lblcardClientsWithOrdersValue.setText(str(stats['clients_with_orders']))

    def _load_recent_orders(self):
        db = Database()
        orders = db.get_recent_orders(limit=5)
        
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
        db = Database()
        orders = db.get_all_orders()
        
        self.ui.tableOrders.setRowCount(0)
        
        if not orders:
            return

        self.ui.tableOrders.setRowCount(len(orders))
        
        for row_idx, order in enumerate(orders):
            item_vessel = QTableWidgetItem(str(order['vessel_code']))
            self.ui.tableOrders.setItem(row_idx, 0, item_vessel)
            
            item_client = QTableWidgetItem(order['client_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 1, item_client)
            
            item_date = QTableWidgetItem(order['order_date'] or '')
            item_date.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 2, item_date)
            
            item_employee = QTableWidgetItem(order['employee_name'] or '')
            self.ui.tableOrders.setItem(row_idx, 3, item_employee)
            
            item_status = QTableWidgetItem(order['status'])
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 4, item_status)
            
            item_completion = QTableWidgetItem('-')
            item_completion.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 5, item_completion)
            
            item_actions = QTableWidgetItem('')
            item_actions.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.ui.tableOrders.setItem(row_idx, 6, item_actions)

    def _load_research_queue(self):
        db = Database()
        research = db.get_research_queue()
        
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