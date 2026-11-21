"""Диалог входа для клиентов."""
import os
import hashlib
from PyQt6.QtWidgets import (
    QDialog, QLineEdit, QCheckBox, QPushButton, QHBoxLayout, QWidget
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from ui.login_client_ui import Ui_ClientLoginWindow
from session import Session, Role
from db import client_repo


def _get_logo_path(filename: str) -> str:
    """Абсолютный путь к файлу в папке logo/ (рядом с этим файлом)."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logo', filename)


def _render_svg(filename: str, size: int = 20) -> QIcon:
    """Рендерит SVG через QSvgRenderer."""
    path = _get_logo_path(filename)
    if not os.path.exists(path):
        print(f"[WARN] Иконка не найдена: {path}")
        return QIcon()
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class ClientLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ClientLoginWindow()
        self.ui.setupUi(self)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()
        self.ui.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.loginButton.clicked.connect(self.login)
        self.ui.emailInput.returnPressed.connect(self.ui.passwordInput.setFocus)
        self.ui.backButton.clicked.connect(self.reject)
        self.ui.forgotPasswordLabel.mousePressEvent = lambda e: self.forgot_password()

        # Меняем placeholder и подпись
        self.ui.emailInput.setPlaceholderText("E-mail или телефон")
        self.ui.emailLabel.setText("E-mail или телефон")

        # === Чекбокс "Запомнить меня" ===
        self._setup_remember_checkbox()

        # === Кнопка-иконка глаза ===
        self._setup_password_toggle()

    def _setup_remember_checkbox(self):
        """Добавить чекбокс 'Запомнить меня' после поля пароля."""
        self.chkRemember = QCheckBox("Запомнить меня")
        self.chkRemember.setChecked(True)
        self.chkRemember.setStyleSheet("""
            QCheckBox {
                color: #2c3e50;
                font-size: 13px;
                spacing: 6px;
                margin-top: 4px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
        """)

        vertical_layout = self.ui.formWidget.layout()
        if vertical_layout:
            idx = vertical_layout.indexOf(self.ui.passwordInput)
            if idx >= 0:
                vertical_layout.insertWidget(idx + 1, self.chkRemember)

    def _setup_password_toggle(self):
        """Создать кнопку-иконку глаза и обернуть поле пароля."""
        self.btnTogglePassword = QPushButton()
        self.btnTogglePassword.setObjectName("btnTogglePassword")
        self.btnTogglePassword.setFixedSize(36, 36)
        self.btnTogglePassword.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btnTogglePassword.setIconSize(QSize(20, 20))
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

        # Оборачиваем passwordInput в горизонтальный контейнер
        vertical_layout = self.ui.formWidget.layout()
        if vertical_layout:
            idx = vertical_layout.indexOf(self.ui.passwordInput)
            if idx >= 0:
                vertical_layout.removeWidget(self.ui.passwordInput)
                container = QWidget()
                container.setObjectName("passwordContainer")
                hlay = QHBoxLayout(container)
                hlay.setContentsMargins(0, 0, 0, 0)
                hlay.setSpacing(4)
                hlay.addWidget(self.ui.passwordInput)
                hlay.addWidget(self.btnTogglePassword)
                vertical_layout.insertWidget(idx, container)

    def _set_eye_icon(self, open: bool):
        filename = 'eye_open.svg' if open else 'eye_close.svg'
        icon = _render_svg(filename, size=20)
        self.btnTogglePassword.setIcon(icon)
        self.btnTogglePassword.setIconSize(QSize(20, 20))

    def _toggle_password(self):
        if self.ui.passwordInput.echoMode() == QLineEdit.EchoMode.Password:
            self.ui.passwordInput.setEchoMode(QLineEdit.EchoMode.Normal)
            self._set_eye_icon(open=True)
        else:
            self.ui.passwordInput.setEchoMode(QLineEdit.EchoMode.Password)
            self._set_eye_icon(open=False)

    def show_error(self, message: str):
        self.ui.lblError.setText(message)
        self.ui.lblError.show()
        self.ui.lblError.raise_()

    def forgot_password(self):
        self.show_error("Обратитесь к администратору для сброса пароля")

    def login(self):
        login_text = self.ui.emailInput.text().strip()
        password = self.ui.passwordInput.text()
        remember = self.chkRemember.isChecked()

        self.ui.lblError.setStyleSheet("color: #B42318;")
        self.ui.lblError.hide()

        if not login_text or not password:
            self.show_error("Введите E-mail/телефон и пароль")
            return

        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            user_client = client_repo.get_client_by_login(login_text, password_hash)

            if user_client:
                Session.set_user(
                    login=user_client.get('email') or user_client.get('phone', ''),
                    role=Role.CLIENT,
                    display_name=user_client['full_name'],
                    user_id=user_client['client_id'],
                    user_type='client',
                    remember=remember,
                )
                self.accept()
                return

            self.show_error("Неверный E-mail/телефон или пароль")
        except Exception as e:
            self.show_error("Ошибка подключения к БД")
            print(e)