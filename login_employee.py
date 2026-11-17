from PyQt6.QtWidgets import QDialog, QLineEdit
from PyQt6.QtGui import QIcon
from ui.login_employee_ui import Ui_EmployeeLoginDialog
from session import Session, Role
from db import base_repo
import hashlib


class EmployeeLoginWindow(QDialog):
    """Окно входа для сотрудников ОТК."""

    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLoginDialog()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()

        self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.btnTogglePassword.setIcon(QIcon("logo/eye_close.svg"))
        self.ui.btnTogglePassword.clicked.connect(self.toggle_password)

        self.ui.btnLogin.clicked.connect(self.login)
        self.ui.btnBack.clicked.connect(self.reject)
        self.ui.editEmail.returnPressed.connect(self.ui.editPassword.setFocus)
        self.ui.editPassword.returnPressed.connect(self.login)

    def toggle_password(self):
        current_mode = self.ui.editPassword.echoMode()
        if current_mode == QLineEdit.EchoMode.Password:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)
            self.ui.btnTogglePassword.setIcon(QIcon("logo/eye_open.svg"))
        else:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
            self.ui.btnTogglePassword.setIcon(QIcon("logo/eye_close.svg"))

    def show_error(self, message):
        self.ui.lblError.setText(message)
        self.ui.lblError.show()
        self.ui.lblError.raise_()

    def login(self):
        login_text = self.ui.editEmail.text().strip()
        password = self.ui.editPassword.text()
        self.ui.lblError.setStyleSheet("color: #B42318;")
        self.ui.lblError.hide()

        if not login_text or not password:
            self.show_error("Введите логин и пароль")
            return

        try:
            base_repo.connect()
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query = """
                SELECT employee_id, full_name, login, role
                FROM employees
                WHERE login = %s AND password_hash = %s AND is_active = 1
            """
            result = base_repo.execute_query(query, (login_text, password_hash))

            if result:
                user = result[0]
                Session.set_user(
                    login=user['login'],
                    role=user['role'],
                    display_name=user['full_name'],
                    user_id=user['employee_id'],
                    user_type='employee'
                )
                self.accept()
                return

            self.show_error("Неверный логин или пароль")
        except Exception as e:
            self.show_error("Ошибка подключения к БД")
            print(e)
