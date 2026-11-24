"""Точка входа в приложение ИС ОТК."""
import sys
import os
import subprocess
import importlib.util

def _ensure_dependencies() -> bool:
    """Проверить и установить зависимости из requirements.txt.
    
    Returns:
        True если зависимости установлены успешно, False при ошибке.
    """
    req_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "requirements.txt")
    if not os.path.exists(req_path):
        return True
    
    try:
        with open(req_path, "r", encoding="utf-8") as f:
            requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]
    except Exception:
        return True
    
    missing = []
    for req in requirements:
        pkg_name = req.split(">=")[0].split("==")[0].split("<=")[0].split(">")[0].split("<")[0].split("~=")[0].strip()
        import_name = pkg_name.replace("-", "_")
        if importlib.util.find_spec(import_name) is None:
            missing.append(req)
    
    if not missing:
        return True
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "--quiet", *missing
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False


from PyQt6.QtWidgets import QApplication, QDialog, QStyleFactory, QMessageBox
from main_window import MainWindow
from client_window import ClientWindow
from choose_login import ChooseLoginDialog
from employee_login import EmployeeLoginDialog
from client_login import ClientLoginDialog
from dialogs.connection_dialog import ConnectionDialog  # <-- диалог подключения к БД
from session import Session
from logger import app_logger
from error_handling import install_excepthook

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


def run_app():
    # Проверить и установить зависимости перед запуском
    if not _ensure_dependencies():
        # Если не получилось установить — показываем ошибку и выходим
        app = QApplication(sys.argv)  # нужно для QMessageBox
        QMessageBox.critical(
            None,
            "Ошибка зависимостей",
            "Не удалось автоматически установить необходимые пакеты.\n"
            "Установите их вручную:\n  pip install -r requirements.txt"
        )
        sys.exit(1)

    # Установить глобальный обработчик исключений
    install_excepthook()

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