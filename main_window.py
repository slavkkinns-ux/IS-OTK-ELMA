from PyQt6.QtWidgets import QMainWindow, QButtonGroup
from ui.main_window_ui import Ui_MainWindow
from session import Session

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
        self._setup_home_tab()
        self._setup_orders_tab()
        self._setup_clients_tab()
        self._setup_research_tab()
        self._setup_reports_tab()

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

    def _setup_home_tab(self):
        self.ui.btnAllOrders.clicked.connect(self._go_to_orders)

    def _setup_orders_tab(self):
        self.ui.btnAddOrder.clicked.connect(self._add_order)
        self.ui.btnEditOrder.clicked.connect(self._edit_order)
        self.ui.btnSearchOrders.clicked.connect(self._search_orders)

    def _setup_clients_tab(self):
        self.ui.btnAddClient.clicked.connect(self._add_client)

    def _setup_research_tab(self):
        self.ui.btnSaveResearchResult.clicked.connect(self._save_research)

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