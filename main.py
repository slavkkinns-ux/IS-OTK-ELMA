import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from login import LoginWindow
from main_window import MainWindow
from session import Session

THEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")

def load_theme(app, theme_name="light"):
    theme_path = os.path.join(THEMES_DIR, f"{theme_name}.qss")
    
    if not os.path.exists(theme_path):
        return
        
    try:
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass

def run_app():
    app = QApplication(sys.argv)
    load_theme(app, "light")

    while True:
        Session.init()

        if Session.is_authenticated():
            window = MainWindow(app)
            window.show()
            
            app.exec()
            
            if not Session.is_authenticated():
                continue
            else:
                break
        else:
            login = LoginWindow()
            if login.exec() == QDialog.DialogCode.Accepted:
                continue
            else:
                sys.exit(0)

if __name__ == "__main__":
    run_app()