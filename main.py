"""Точка входа в приложение ИС ОТК."""
import sys
import os
from PyQt6.QtWidgets import QApplication, QDialog, QStyleFactory
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
from employee_login import EmployeeLoginDialog
from client_login import ClientLoginDialog
from dialogs.connection_dialog import ConnectionDialog  # <-- диалог подключения к БД
from session import Session
from datetime import datetime, date
from logger import app_logger

THEMES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "styles")


def load_theme(app, theme_name="light"):
    """Загрузить QSS-тему."""
    theme_path = os.path.join(THEMES_DIR, f"{theme_name}.qss")
    if not os.path.exists(theme_path):
        return
    try:
        with open(theme_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    except Exception:
        pass


def format_date(value) -> str:
    """Безопасно форматирует дату/дата-время в строку вида ДД.ММ.ГГГГ."""
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return str(value)


def run_app():
    app_logger.info("=" * 60)
    app_logger.info("Приложение ИС ОТК запускается")
    app_logger.info("=" * 60)
    os.environ["QT_QPA_PLATFORMTHEME"] = ""

    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create("Fusion"))
    load_theme(app, "light")

    # =========================================================================
    # 1. Подключение к БД (до авторизации)
    # =========================================================================
    db_dialog = ConnectionDialog()
    if db_dialog.exec() != ConnectionDialog.DialogCode.Accepted:
        # Пользователь нажал "Выйти" или закрыл диалог
        sys.exit(0)
    # Если дошли сюда — соединение установлено (ConnectionDialog сам вызвал connect())

    # =========================================================================
    # 2. Цикл авторизации
    # =========================================================================
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
                # Выход из системы — возвращаемся к выбору входа
                continue
            else:
                # Нормальное завершение
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