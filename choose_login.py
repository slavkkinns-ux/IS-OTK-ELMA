from PyQt6.QtWidgets import QDialog
from PyQt6.QtCore import Qt
from ui.choose_login_ui import Ui_ChooseLoginDialog


class ChooseLoginDialog(QDialog):
    """
    Диалог выбора типа входа: Сотрудник или Клиент.
    Возвращает:
        - "employee" если выбрали вход сотрудника
        - "client" если выбрали вход клиента
        - None если закрыли окно
    """

    def __init__(self):
        super().__init__()
        self.ui = Ui_ChooseLoginDialog()
        self.ui.setupUi(self)

        # Включаем отрисовку фона по stylesheet
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Применяем стили
        self._apply_styles()

        self.choice = None

        # Подключаем кнопки
        self.ui.btnEmployeeLogin.clicked.connect(self._choose_employee)
        self.ui.btnClientLogin.clicked.connect(self._choose_client)

    def _apply_styles(self):
        """Применяет стили к каждому виджету индивидуально"""
        self.setStyleSheet("""
            QDialog#ChooseLoginDialog {
                background-color: #F4F7FA;
            }
        """)

        self.ui.headerFrame.setStyleSheet("""
            QFrame#headerFrame {
                background-color: #173B60;
                border-radius: 14px;
            }
        """)

        self.ui.lblLogo.setStyleSheet("color: white; font-weight: bold;")
        self.ui.lblSystemName.setStyleSheet("color: #D7E7F6;")
        self.ui.lblWelcome.setStyleSheet("color: white; font-weight: bold;")
        self.ui.lblSubtitle.setStyleSheet("color: #D7E7F6;")

        self.ui.employeeCard.setStyleSheet("""
            QFrame#employeeCard {
                background-color: white;
                border: 1px solid #DCE4EC;
                border-radius: 12px;
            }
        """)
        self.ui.lblEmployeeIcon.setStyleSheet("color: #245A91;")
        self.ui.lblEmployeeTitle.setStyleSheet("color: #000000; font-weight: bold;")
        self.ui.lblEmployeeDescription.setStyleSheet("color: #000000;")
        self.ui.btnEmployeeLogin.setStyleSheet("""
            QPushButton#btnEmployeeLogin {
                background-color: #245A91;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 11px;
                font-weight: bold;
            }
            QPushButton#btnEmployeeLogin:hover {
                background-color: #1B466F;
            }
        """)

        self.ui.clientCard.setStyleSheet("""
            QFrame#clientCard {
                background-color: white;
                border: 1px solid #DCE4EC;
                border-radius: 12px;
            }
        """)
        self.ui.lblClientIcon.setStyleSheet("color: #245A91;")
        self.ui.lblClientTitle.setStyleSheet("color: #000000; font-weight: bold;")
        self.ui.lblClientDescription.setStyleSheet("color: #000000;")
        self.ui.btnClientLogin.setStyleSheet("""
            QPushButton#btnClientLogin {
                background-color: #245A91;
                color: white;
                border: none;
                border-radius: 7px;
                padding: 11px;
                font-weight: bold;
            }
            QPushButton#btnClientLogin:hover {
                background-color: #1B466F;
            }
        """)

        self.ui.lblFooter.setStyleSheet("color: rgb(162, 162, 162);")

    def _choose_employee(self):
        self.choice = "employee"
        self.accept()

    def _choose_client(self):
        self.choice = "client"
        self.accept()

    @staticmethod
    def get_choice():
        """Статический метод для удобного вызова.
        Возвращает 'employee', 'client' или None."""
        dialog = ChooseLoginDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.choice
        return None
