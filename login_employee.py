"""Диалог входа для сотрудников."""
import os
from PyQt6.QtWidgets import QDialog, QLineEdit, QCheckBox, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon
from ui.login_employee_ui import Ui_EmployeeLoginDialog
from session import Session, Role
from db import connection
import hashlib


def _get_logo_path(filename: str) -> str:
    """Абсолютный путь к файлу в папке logo/."""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        'logo', filename
    )


class EmployeeLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLoginDialog()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()
        self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.btnLogin.clicked.connect(self.login)
        self.ui.editEmail.returnPressed.connect(self.ui.editPassword.setFocus)
        self.ui.btnBack.clicked.connect(self.reject)

        # === 1. Чекбокс "Запомнить меня" ===
        # Ищем существующий чекбокс в UI (может быть "Запомнить корпоративную почту")
        existing_checkboxes = self.findChildren(QCheckBox)
        if existing_checkboxes:
            self.chkRemember = existing_checkboxes[0]
            self.chkRemember.setText("Запомнить меня")
        else:
            # Если чекбокса нет — создаём и вставляем перед кнопкой входа
            self.chkRemember = QCheckBox("Запомнить меня")
            self.chkRemember.setChecked(True)
            parent_layout = self.ui.btnLogin.parent().layout()
            if parent_layout:
                idx = parent_layout.indexOf(self.ui.btnLogin)
                if idx >= 0:
                    parent_layout.insertWidget(idx, self.chkRemember)
        self.chkRemember.setChecked(True)

        # === 2. Кнопка показа пароля — иконка глаза ===
        # Ищем существующую кнопку btnTogglePassword в UI
        self.btnTogglePassword = self.findChild(QPushButton, "btnTogglePassword")
        if self.btnTogglePassword:
            # Кнопка уже есть в UI — просто меняем её на иконку
            self.btnTogglePassword.setCheckable(True)
            self.btnTogglePassword.setText("")  # убираем текст
            self.btnTogglePassword.setFixedSize(32, 32)
            self.btnTogglePassword.setCursor(Qt.CursorShape.PointingHandCursor)
            self.btnTogglePassword.setStyleSheet("""
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 4px;
                }
                QPushButton:hover {
                    background-color: #eaf2f8;
                    border-radius: 6px;
                }
            """)
            self.btnTogglePassword.clicked.connect(self._toggle_password)
            self._set_eye_icon(open=False)  # начальное состояние — пароль скрыт
        else:
            # Кнопки нет — создаём и вставляем справа от поля пароля
            self._create_password_toggle_button()

    def _create_password_toggle_button(self):
        """Создать кнопку-иконку и вставить справа от поля пароля."""
        self.btnTogglePassword = QPushButton()
        self.btnTogglePassword.setObjectName("btnTogglePassword")
        self.btnTogglePassword.setFixedSize(32, 32)
        self.btnTogglePassword.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnTogglePassword.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 4px;
            }
            QPushButton:hover {
                background-color: #eaf2f8;
                border-radius: 6px;
            }
        """)
        self.btnTogglePassword.clicked.connect(self._toggle_password)
        self._set_eye_icon(open=False)

        # Оборачиваем editPassword в горизонтальный контейнер
        from PyQt6.QtWidgets import QHBoxLayout, QWidget
        parent = self.ui.editPassword.parent()
        layout = parent.layout() if parent else None
        if layout:
            idx = layout.indexOf(self.ui.editPassword)
            if idx >= 0:
                layout.removeWidget(self.ui.editPassword)
                container = QWidget()
                container.setObjectName("passwordContainer")
                hlay = QHBoxLayout(container)
                hlay.setContentsMargins(0, 0, 0, 0)
                hlay.setSpacing(4)
                hlay.addWidget(self.ui.editPassword)
                hlay.addWidget(self.btnTogglePassword)
                layout.insertWidget(idx, container)

    def _set_eye_icon(self, open: bool):
        """Установить иконку глаза."""
        filename = 'eye_open.svg' if open else 'eye_close.svg'
        path = _get_logo_path(filename)
        if os.path.exists(path):
            icon = QIcon(path)
            pixmap = icon.pixmap(QSize(20, 20))
            self.btnTogglePassword.setIcon(pixmap)
            self.btnTogglePassword.setIconSize(QSize(20, 20))
        else:
            self.btnTogglePassword.setText("👁" if open else "🙈")
            self.btnTogglePassword.setIcon(QIcon())

    def _toggle_password(self):
        """Переключить режим отображения пароля."""
        if self.ui.editPassword.echoMode() == QLineEdit.EchoMode.Password:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)
            self._set_eye_icon(open=True)
        else:
            self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
            self._set_eye_icon(open=False)

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
            conn = connection.get_connection()
            password_hash = hashlib.sha256(password.encode()).hexdigest()

            with conn.cursor() as cur:
                cur.execute("""
                    SELECT employee_id, full_name, login, role
                    FROM employees
                    WHERE login = %s AND password_hash = %s AND is_active = 1
                """, (email, password_hash))
                user = cur.fetchone()

            if user:
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