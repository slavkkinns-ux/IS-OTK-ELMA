from PyQt6.QtWidgets import QDialog, QLineEdit
from PyQt6.QtGui import QIcon
from ui.login_client_ui import Ui_ClientLoginWindow
from session import Session, Role
from db import client_repo
import hashlib


class ClientLoginWindow(QDialog):
    """Окно входа для клиентов."""

    def __init__(self):
        super().__init__()
        self.ui = Ui_ClientLoginWindow()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()

        self.ui.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.loginButton.clicked.connect(self.login)
        self.ui.backButton.clicked.connect(self.reject)
        self.ui.emailInput.returnPressed.connect(self.ui.passwordInput.setFocus)
        self.ui.passwordInput.returnPressed.connect(self.login)

    def show_error(self, message):
        self.ui.lblError.setText(message)
        self.ui.lblError.show()

    def login(self):
        login_text = self.ui.emailInput.text().strip()
        password = self.ui.passwordInput.text()
        self.ui.lblError.setStyleSheet("color: #B42318;")
        self.ui.lblError.hide()

        if not login_text or not password:
            self.show_error("Введите логин и пароль")
            return

        try:
            client_repo.connect()
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            user_client = client_repo.get_client_by_login(login_text, password_hash)
            if user_client:
                Session.set_user(
                    login=user_client['login'],
                    role=Role.CLIENT,
                    display_name=user_client['full_name'],
                    user_id=user_client['client_id'],
                    user_type='client'
                )
                self.accept()
                return

            self.show_error("Неверный логин или пароль")
        except Exception as e:
            self.show_error("Ошибка подключения к БД")
            print(e)
