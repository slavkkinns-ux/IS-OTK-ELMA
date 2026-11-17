import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QStyleFactory
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
from employee_login import EmployeeLoginDialog
from client_login import ClientLoginDialog
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
    os.environ["QT_QPA_PLATFORMTHEME"] = ""
    
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    load_theme(app, "light")
    
    while True:
        Session.init()
        
        if Session.is_authenticated():
            user = Session.get_user()
            user_type = user.get("user_type", "employee") if user else "employee"
            
            if user_type == "client":
                window = ClientWindow()
            else:
                window = MainWindow(app)
            
            window.show()
            app.exec()
            
            if not Session.is_authenticated():
                continue
            else:
                break
        else:
            # 1. Показываем выбор типа входа
            choice = ChooseLoginDialog.get_choice()
            
            if choice is None:
                sys.exit(0)
            
            # 2. Показываем соответствующий диалог входа
            while True:
                if choice == "employee":
                    login_dialog = EmployeeLoginDialog()
                else:
                    login_dialog = ClientLoginDialog()
                
                result = login_dialog.exec()
                
                if result == QDialog.DialogCode.Accepted:
                    break
                else:
                    break
            
            continue

if __name__ == "__main__":
    run_app()