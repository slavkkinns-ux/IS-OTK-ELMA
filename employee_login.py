"""Диалог входа для сотрудников."""

from __future__ import annotations

import logging
import os
from PyQt6.QtWidgets import QDialog, QLineEdit, QCheckBox, QPushButton
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap, QPainter
from PyQt6.QtSvg import QSvgRenderer
from ui.login_employee_ui import Ui_EmployeeLoginDialog
from session import Session
from services.employee_service import EmployeeService
from db import employee_repo as _default_employee_repo
from utils.files import get_resource_path

logger = logging.getLogger(__name__)


def _get_logo_path(filename: str) -> str:
    """Абсолютный путь к файлу в папке logo/ (работает в dev и в EXE)."""
    return get_resource_path(os.path.join('logo', filename))


def _render_svg(filename: str, size: int = 20) -> QIcon:
    """Рендерит SVG через QSvgRenderer."""
    path = _get_logo_path(filename)
    if not os.path.exists(path):
        logger.warning("Иконка не найдена: %s", path)
        return QIcon()
    renderer = QSvgRenderer(path)
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)


class EmployeeLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_EmployeeLoginDialog()
        self.ui.setupUi(self)

        # Dependency Injection
        self.employee_service = EmployeeService(_default_employee_repo)

        self.ui.lblError.setText("")
        self.ui.lblError.hide()
        self.ui.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.ui.btnLogin.clicked.connect(self.login)
        self.ui.editEmail.returnPressed.connect(self.ui.editPassword.setFocus)
        self.ui.btnBack.clicked.connect(self.reject)

        # === Чекбокс "Запомнить меня" ===
        self._setup_remember_checkbox()

        # === Кнопка-иконка глаза ===
        self._setup_password_toggle()

    def _setup_remember_checkbox(self):
        """Ищет существующий чекбокс в UI и переименовывает его."""
        existing = self.findChildren(QCheckBox)
        if existing:
            self.chkRemember = existing[0]
            self.chkRemember.setText("Запомнить меня")
        else:
            self.chkRemember = QCheckBox("Запомнить меня")
            self.chkRemember.setChecked(True)
            parent = self.ui.btnLogin.parent()
            layout = parent.layout() if parent else None
            if layout:
                idx = layout.indexOf(self.ui.btnLogin)
                if idx >= 0:
                    layout.insertWidget(idx, self.chkRemember)
        self.chkRemember.setChecked(True)

    def _setup_password_toggle(self):
        """Настраивает кнопку показа пароля — иконка глаза."""
        btn = self.findChild(QPushButton, "btnTogglePassword")
        if not btn:
            logger.warning("btnTogglePassword не найден в UI")
            return

        self.btnTogglePassword = btn
        self.btnTogglePassword.setCheckable(True)
        self.btnTogglePassword.setText("")
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

    def _set_eye_icon(self, open: bool):
        filename = 'eye_open.svg' if open else 'eye_close.svg'
        icon = _render_svg(filename, size=20)
        self.btnTogglePassword.setIcon(icon)
        self.btnTogglePassword.setIconSize(QSize(20, 20))

    def _toggle_password(self):
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
            user = self.employee_service.authenticate_employee(email, password)

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
        except Exception as exc:
            logger.error("Ошибка входа сотрудника: %s", exc)
            self.show_error("Ошибка подключения к БД")


__all__ = ["EmployeeLoginDialog"]
