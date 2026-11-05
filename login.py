from PyQt6.QtWidgets import QDialog, QLineEdit
from PyQt6.QtGui import QIcon
from ui.login_ui import Ui_LoginDialog
from session import Session, Role
from db import Database
from config import DB_CONFIG
import hashlib

class LoginWindow(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_LoginDialog()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()

        self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.btnTogglePassword.setIcon(QIcon("logo/eye_close.svg"))
        self.ui.btnTogglePassword.clicked.connect(self.toggle_password)

        self.ui.btnLogin.clicked.connect(self.login)
        self.ui.editLogin.returnPressed.connect(self.ui.editPassword.setFocus)

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
        login = self.ui.editLogin.text().strip()
        password = self.ui.editPassword.text()
        self.ui.lblError.setStyleSheet("color: red;")
        self.ui.lblError.hide()

        if not login or not password:
            self.show_error("Введите логин и пароль")
            return

        try:
            db = Database()
            db.connect()
            
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            query = """
                SELECT employee_id, full_name, login, role 
                FROM employees 
                WHERE login = %s AND password_hash = %s AND is_active = 1
            """
            result = db.execute_query(query, (login, password_hash))
            
            if result:
                user = result[0]
                Session.set_user(
                    login=user['login'],
                    role=user['role'],
                    display_name=user['full_name'],
                    employee_id=user['employee_id']
                )
                self.accept()
            else:
                self.show_error("Неверный логин или пароль")
                
        except Exception as e:
            self.show_error(f"Ошибка подключения к БД")
            print(e)