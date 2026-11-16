from PyQt6.QtWidgets import QDialog
from ui.choose_login_ui import Ui_ChooseLoginDialog


class ChooseLoginDialog(QDialog):
    """
    Диалог выбора типа входа: Сотрудник или Клиент.
    Возвращает:
        - "employee" если выбрали вход сотрудника
        - "client" если выбрали вход клиента
        - None если закрыли окно
    """
    
    # Стили с высокой специфичностью (привязка к #ChooseLoginDialog),
    # чтобы перекрыть глобальную тему приложения
    DIALOG_STYLE = """
    QDialog#ChooseLoginDialog {
        background-color: #F4F7FA;
    }
    QDialog#ChooseLoginDialog QFrame#headerFrame {
        background-color: #173B60;
        border-radius: 14px;
    }
    QDialog#ChooseLoginDialog QLabel#lblLogo,
    QDialog#ChooseLoginDialog QLabel#lblWelcome {
        color: white;
        font-weight: bold;
    }
    QDialog#ChooseLoginDialog QLabel#lblSystemName,
    QDialog#ChooseLoginDialog QLabel#lblSubtitle {
        color: #D7E7F6;
    }
    QDialog#ChooseLoginDialog QFrame#employeeCard,
    QDialog#ChooseLoginDialog QFrame#clientCard {
        background-color: white;
        border: 1px solid #DCE4EC;
        border-radius: 12px;
    }
    QDialog#ChooseLoginDialog QLabel#lblEmployeeIcon,
    QDialog#ChooseLoginDialog QLabel#lblClientIcon {
        color: #245A91;
    }
    QDialog#ChooseLoginDialog QLabel#lblEmployeeTitle,
    QDialog#ChooseLoginDialog QLabel#lblClientTitle,
    QDialog#ChooseLoginDialog QLabel#lblEmployeeDescription,
    QDialog#ChooseLoginDialog QLabel#lblClientDescription {
        color: #000000;
    }
    QDialog#ChooseLoginDialog QPushButton#btnEmployeeLogin,
    QDialog#ChooseLoginDialog QPushButton#btnClientLogin {
        background-color: #245A91;
        color: white;
        border: none;
        border-radius: 7px;
        padding: 11px;
        font-weight: bold;
    }
    QDialog#ChooseLoginDialog QPushButton#btnEmployeeLogin:hover,
    QDialog#ChooseLoginDialog QPushButton#btnClientLogin:hover {
        background-color: #1B466F;
    }
    QDialog#ChooseLoginDialog QLabel#lblFooter {
        color: rgb(162, 162, 162);
    }
    """

    def __init__(self):
        super().__init__()
        self.ui = Ui_ChooseLoginDialog()
        self.ui.setupUi(self)
        
        # Принудительно применяем стили к диалогу
        self.setStyleSheet(self.DIALOG_STYLE)
        
        self.choice = None
        
        # Подключаем кнопки
        self.ui.btnEmployeeLogin.clicked.connect(self._choose_employee)
        self.ui.btnClientLogin.clicked.connect(self._choose_client)
    
    def _choose_employee(self):
        self.choice = "employee"
        self.accept()
    
    def _choose_client(self):
        self.choice = "client"
        self.accept()
    
    @staticmethod
    def get_choice():
        """Статический метод для удобного вызова"""
        dialog = ChooseLoginDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.choice
        return None