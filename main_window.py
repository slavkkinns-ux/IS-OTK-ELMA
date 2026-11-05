from PyQt6.QtWidgets import QMainWindow
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

        self.ui.btnExit.clicked.connect(self.logout)

        self.ui.btnHome.clicked.connect(lambda: self.show_page(self.ui.pageHome))
        self.ui.btnOrders.clicked.connect(lambda: self.show_page(self.ui.pageOrders))
        self.ui.btnClients.clicked.connect(lambda: self.show_page(self.ui.pageClients))
        self.ui.btnResearch.clicked.connect(lambda: self.show_page(self.ui.pageResearch))
        self.ui.btnReports.clicked.connect(lambda: self.show_page(self.ui.pageReports))

    def logout(self):
        Session.clear()
        self.close()

    def show_page(self, page):
        self.ui.stackedWidget.setCurrentWidget(page)