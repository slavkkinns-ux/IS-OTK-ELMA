"""Диалог добавления/редактирования сотрудника."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QWidget,
)

from db import employee_repo as _default_employee_repo
from services.employee_service import EmployeeService
from session import Session
from widgets.base_dialog import BaseDialog
from widgets.styles import INFO_PANEL_STYLE

ROLE_DISPLAY: dict[str, str] = {
    'manager': 'Менеджер',
    'lab_technician': 'Лаборант',
    'controller': 'Контролёр',
    'admin': 'Администратор',
}

ROLE_DESCRIPTIONS: dict[str, str] = {
    'manager': '✓ Создание заказов\n✓ Просмотр заказов\n✗ Исследования\n✗ Отчёты',
    'lab_technician': '✓ Создание заказов\n✓ Просмотр заказов\n✓ Исследования\n✓ Отчёты',
    'controller': '✓ Создание заказов\n✓ Просмотр заказов\n✓ Исследования\n✓ Отчёты',
    'admin': '✓ Все функции\n✓ Управление сотрудниками\n✓ Просмотр логов',
}


class EmployeeDialog(BaseDialog):
    """Диалог добавления или редактирования сотрудника.

    Сохраняет данные сам через EmployeeService и закрывается с Accepted.
    Вызывающий код после Accepted только обновляет список.
    """

    def __init__(self, parent: QWidget | None = None, employee_id: int | None = None,
                 employee_service: EmployeeService | None = None) -> None:
        super().__init__(
            parent,
            title="Редактирование сотрудника" if employee_id else "Добавление сотрудника",
            min_width=500,
        )
        self.employee_id = employee_id
        self.service = employee_service or EmployeeService(_default_employee_repo)

        self._init_ui()
        if employee_id:
            self._load_employee_data()

    def _init_ui(self) -> None:
        form_group = QGroupBox("Данные сотрудника")
        form = QFormLayout(form_group)

        self.edit_full_name = QLineEdit()
        self.edit_full_name.setPlaceholderText("Иванов Иван Иванович")
        form.addRow("ФИО *:", self.edit_full_name)

        self.edit_login = QLineEdit()
        self.edit_login.setPlaceholderText("ivanov")
        form.addRow("Логин *:", self.edit_login)

        self.edit_password: QLineEdit | None = None
        if not self.employee_id:
            self.edit_password = QLineEdit()
            self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.edit_password.setPlaceholderText("Минимум 6 символов")
            form.addRow("Пароль *:", self.edit_password)

        self.combo_role = QComboBox()
        for role_key, role_name in ROLE_DISPLAY.items():
            self.combo_role.addItem(role_name, role_key)
        self.combo_role.currentIndexChanged.connect(self._on_role_changed)
        form.addRow("Роль *:", self.combo_role)

        self.check_active = QCheckBox("Активен")
        self.check_active.setChecked(True)
        form.addRow("Статус:", self.check_active)

        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("email@example.com")
        form.addRow("Email:", self.edit_email)

        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("+7 (999) 123-45-67")
        form.addRow("Телефон:", self.edit_phone)

        self.root.addWidget(form_group)

        self.lbl_role_description = QLabel()
        self.lbl_role_description.setStyleSheet(INFO_PANEL_STYLE)
        self.root.addWidget(self.lbl_role_description)

        self.add_save_cancel_buttons(self._save)
        self._on_role_changed(0)

    def _on_role_changed(self, index: int) -> None:
        role_key = self.combo_role.itemData(index)
        if role_key:
            self.lbl_role_description.setText(
                f"<b>{ROLE_DISPLAY[role_key]}:</b><br>"
                + ROLE_DESCRIPTIONS[role_key].replace("\n", "<br>")
            )

    def _load_employee_data(self) -> None:
        emp = self.service.get_employee_by_id(self.employee_id)
        if not emp:
            return

        self.edit_full_name.setText(emp.get('full_name', ''))
        self.edit_login.setText(emp.get('login', ''))
        self.edit_login.setReadOnly(True)
        self.check_active.setChecked(bool(emp.get('is_active', 1)))
        self.edit_email.setText(emp.get('email', '') or '')
        self.edit_phone.setText(emp.get('phone', '') or '')

        index = self.combo_role.findData(emp.get('role', 'lab_technician'))
        if index >= 0:
            self.combo_role.setCurrentIndex(index)

    def _save(self) -> None:
        """Сохранить сотрудника. Ошибки валидации сервиса показывает BaseDialog."""
        current_user_id = Session.get_user_id() or 0
        common = {
            "full_name": self.edit_full_name.text().strip(),
            "login": self.edit_login.text().strip(),
            "role": self.combo_role.currentData(),
            "is_active": self.check_active.isChecked(),
            "email": self.edit_email.text().strip() or None,
            "phone": self.edit_phone.text().strip() or None,
        }

        if self.employee_id:
            self.service.update_employee(
                employee_id=self.employee_id,
                current_user_id=current_user_id,
                **common,
            )
        else:
            assert self.edit_password is not None
            self.service.create_employee(
                password=self.edit_password.text(),
                created_by=current_user_id,
                **common,
            )
        self.accept()


__all__ = ["EmployeeDialog", "ROLE_DISPLAY", "ROLE_DESCRIPTIONS"]
