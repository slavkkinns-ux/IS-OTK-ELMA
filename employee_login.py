from PyQt6.QtWidgets import QDialog, QLineEdit, QCheckBox
from ui.login_employee_ui import Ui_EmployeeLoginDialog
from session import Session
from db import base_repo
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
        self.ui.btnBack.clicked.connect(self.reject)

        # Используем СУЩЕСТВУЮЩИЙ чекбокс из UI (не создаём новый)
        self.chkRemember = self._find_remember_checkbox()

    def _find_remember_checkbox(self) -> QCheckBox:
        """Находит чекбокс 'Запомнить...' в UI и переименовывает его."""
        boxes = self.findChildren(QCheckBox)
        if boxes:
            cb = boxes[0]
            cb.setText("Запомнить меня")
            cb.setChecked(True)
            return cb
        # Если в UI чекбокса нет — создаём запасной (на всякий случай)
        cb = QCheckBox("Запомнить меня", self)
        cb.setChecked(True)
        lay = self.layout()
        if lay:
            idx = lay.indexOf(self.ui.btnLogin)
            lay.insertWidget(idx if idx >= 0 else lay.count(), cb)
        return cb

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
        remember = self.chkRemember.isChecked()

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
            result_employee = base_repo.execute_query(
                query_employee, (email, password_hash)
            )

            if result_employee:
                user = result_employee[0]
                Session.set_user(
                    login=user['login'],
                    role=user['role'],
                    display_name=user['full_name'],
                    user_id=user['employee_id'],
                    user_type='employee',
                    remember=remember,
                )
                self.accept()
                return

            self.show_error("Неверная почта или пароль")
        except Exception as e:
            self.show_error("Ошибка подключения к БД")
            print(e)