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
            self.ui.btnHome,
            self.ui.btnOrders,
            self.ui.btnClients,
            self.ui.btnResearch,
            self.ui.btnReports
        ]
        
        for btn in nav_buttons:
            self.nav_group.addButton(btn)
            btn.setCheckable(True)
            btn.setStyleSheet("")
        self.ui.btnHome.setChecked(True)

        self.nav_group.buttonClicked.connect(self._on_nav_clicked)

        self.ui.btnExit.clicked.connect(self.logout)

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