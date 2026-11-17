import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog
from login import LoginWindow
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
from session import Session

def run_app():
    app = QApplication(sys.argv)

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