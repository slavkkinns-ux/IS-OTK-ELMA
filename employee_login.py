from PyQt6.QtWidgets import QDialog, QLineEdit
from PyQt6.QtGui import QIcon
from ui.login_employee_ui import Ui_EmployeeLoginDialog
from session import Session, Role
from db import base_repo, client_repo
import hashlib


class EmployeeLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLoginDialog()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()

        self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.btnTogglePassword.setCheckable(True)
        self.ui.btnTogglePassword.setText("Показать")
        self.ui.btnTogglePassword.clicked.connect(self.toggle_password)

        self.ui.btnLogin.clicked.connect(self.login)
        self.ui.editEmail.returnPressed.connect(self.ui.editPassword.setFocus)
        self.ui.btnBack.clicked.connect(self.reject)  # Возврат к выбору типа входа

    def toggle_password(self, checked: bool):
        if checked:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)
            self.ui.btnTogglePassword.setText("Скрыть")
        else:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
            self.ui.btnTogglePassword.setText("Показать")

    def show_error(self, message: str):
        self.ui.lblError.setText(message)
        self.ui.lblError.show()
        self.ui.lblError.raise_()

    def login(self):
        email = self.ui.editEmail.text().strip()
        password = self.ui.editPassword.text()
        self.ui.lblError.setStyleSheet("color: #B42318;")
        self.ui.lblError.hide()

        if not email or not password:
            self.show_error("Введите корпоративную почту и пароль")
            return

        try:
            base_repo.connect()
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            query_employee = """
                SELECT employee_id, full_name, login, role 
                FROM employees 
                WHERE login = %s AND password_hash = %s AND is_active = 1
            """
            result_employee = base_repo.execute_query(query_employee, (email, password_hash))

            if result_employee:
                user = result_employee[0]
                Session.set_user(
                    login=user['login'],
                    role=user['role'],
                    display_name=user['full_name'],
                    user_id=user['employee_id'],
                    user_type='employee'
                )
                self.accept()
                return

            self.show_error("Неверная почта или пароль")

        except Exception as e:
            self.show_error("Ошибка подключения к БД")
            print(e)