import sys
import os
from PyQt6.QtWidgets import QApplication
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
from session import Session


def run_app():
    app = QApplication(sys.argv)
    # Не завершать приложение при закрытии промежуточных окон
    # (например, окна входа при возврате к выбору типа входа)
    app.setQuitOnLastWindowClosed(False)

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
            # Сначала показываем выбор типа пользователя и окно входа
            choice = ChooseLoginDialog.get_choice()

            if choice is None:
                # Пользователь закрыл окно выбора - выход из приложения
                sys.exit(0)

            # Вход уже выполнен внутри ChooseLoginDialog,
            # повторно показывать окно входа не требуется
            continue

if __name__ == "__main__":
    run_app()
