import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QStyleFactory
from login import LoginWindow
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
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
    # Устанавливаем стиль Fusion ДО создания QApplication
    # Это унифицирует рендеринг между Qt Designer и запуском
    os.environ["QT_QPA_PLATFORMTHEME"] = ""
    
    app = QApplication(sys.argv)
    
    # Применяем стиль Fusion
    app.setStyle(QStyleFactory.create("Fusion"))
    
    # Загружаем тему (QSS поверх Fusion)
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
            # Сначала показываем выбор типа пользователя
            choice = ChooseLoginDialog.get_choice()
            
            if choice is None:
                # Пользователь закрыл окно выбора - выход из приложения
                sys.exit(0)
            
            # Показываем окно входа
            login = LoginWindow()
            
            if login.exec() == QDialog.DialogCode.Accepted:
                continue
            else:
                # Пользователь отменил вход - возвращаемся к выбору типа пользователя
                continue

if __name__ == "__main__":
    run_app()