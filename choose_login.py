"""Диалог выбора типа входа: Сотрудник или Клиент."""
import os
from PyQt6.QtWidgets import QDialog, QSizePolicy
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QIcon, QPixmap
from ui.choose_login_ui import Ui_ChooseLoginDialog
from utils.files import get_resource_path


class ChooseLoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ChooseLoginDialog()
        self.ui.setupUi(self)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._apply_styles()
        self._fix_icons()
        self.choice = None
        self.ui.btnEmployeeLogin.clicked.connect(self._choose_employee)
        self.ui.btnClientLogin.clicked.connect(self._choose_client)

    def _get_logo_path(self, filename: str) -> str:
        """Абсолютный путь к файлу в папке logo/ (работает в dev и в EXE)."""
        return get_resource_path(os.path.join('logo', filename))

    def _fix_icons(self):
        """Заменяет pixmap у иконок и выравнивает их по центру карточки."""
        ICON_SIZE = QSize(48, 48)

        # Настраиваем обе метки иконок одинаково
        for label in (self.ui.lblEmployeeIcon, self.ui.lblClientIcon):
            # Растягиваем метку по горизонтали на всю ширину карточки
            label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.Fixed,
            )
            # Фиксированная высота
            label.setFixedHeight(60)
            # Выравнивание содержимого по центру
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # Убираем цветовой стиль (он для текста, а у нас pixmap)
            label.setStyleSheet("")

        # Иконка сотрудника
        emp_path = self._get_logo_path('briefcase-business.svg')
        if os.path.exists(emp_path):
            icon = QIcon(emp_path)
            pixmap = icon.pixmap(ICON_SIZE)
            pixmap = pixmap.scaled(
                ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.ui.lblEmployeeIcon.setPixmap(pixmap)

        # Иконка клиента
        client_path = self._get_logo_path('users.svg')
        if os.path.exists(client_path):
            icon = QIcon(client_path)
            pixmap = icon.pixmap(ICON_SIZE)
            pixmap = pixmap.scaled(
                ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            self.ui.lblClientIcon.setPixmap(pixmap)

    def _apply_styles(self):
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
        dialog = ChooseLoginDialog()
        result = dialog.exec()
        if result == QDialog.DialogCode.Accepted:
            return dialog.choice
        return None