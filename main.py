import sys
import os
<<<<<<< HEAD
from PyQt6.QtWidgets import QApplication, QDialog, QStyleFactory
=======
from PyQt6.QtWidgets import QApplication, QStyleFactory
>>>>>>> e1dc5e51adc1f446746c36e9e9ea8dd6a7b70588
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
<<<<<<< HEAD
    app.setStyle(QStyleFactory.create("Fusion"))
=======
    # Не завершать приложение при закрытии промежуточных окон
    # (например, окна входа при возврате к выбору типа входа)
    app.setQuitOnLastWindowClosed(False)

    # Применяем стиль Fusion
    app.setStyle(QStyleFactory.create("Fusion"))

    # Загружаем тему (QSS поверх Fusion)
>>>>>>> e1dc5e51adc1f446746c36e9e9ea8dd6a7b70588
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
<<<<<<< HEAD
            # 1. Показываем выбор типа входа
=======
            # Сначала показываем выбор типа пользователя и окно входа
>>>>>>> e1dc5e51adc1f446746c36e9e9ea8dd6a7b70588
            choice = ChooseLoginDialog.get_choice()

            if choice is None:
                sys.exit(0)
<<<<<<< HEAD
            
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
=======

            # Вход уже выполнен внутри ChooseLoginDialog,
            # повторно показывать окно входа не требуется
            continue

>>>>>>> e1dc5e51adc1f446746c36e9e9ea8dd6a7b70588

if __name__ == "__main__":
    run_app()
