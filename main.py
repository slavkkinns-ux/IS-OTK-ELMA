import sys
from PyQt6.QtWidgets import QApplication, QDialog
from login import LoginWindow
from main_window import MainWindow
from session import Session

def run_app():
    app = QApplication(sys.argv)

    while True:
        Session.init()

        if Session.is_authenticated():
            window = MainWindow(app)
            window.show()

            if not Session.is_authenticated():
                continue
            else:
                break
        else:
            login = LoginWindow()
            if login.exec() == QDialog.DialogCode.Accepted:
                continue
            else:
                return sys.exit(0)

if __name__ == "__main__":
    run_app()