"""Диалоги клиентов: добавление, редактирование, просмотр."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QComboBox, QDateEdit, QFormLayout, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QPushButton, QStackedWidget, QWidget,
)

from db import client_repo as _default_client_repo
from services.client_service import ClientService
from utils.passwords import generate_password
from widgets.base_dialog import BaseDialog

# (ключ, подпись) для полей формы
_UL_FIELDS: list[tuple[str, str]] = [
    ("name", "Название компании:"), ("address", "Адрес:"), ("inn", "ИНН:"),
    ("kpp", "КПП:"), ("bank_account", "Расчётный счёт:"), ("bik", "БИК:"),
    ("director_name", "ФИО руководителя:"), ("contact_person", "ФИО контактного лица:"),
    ("phone", "Телефон:"), ("email", "E-mail:"),
]
_FL_TEXT_FIELDS: list[tuple[str, str]] = [
    ("name", "ФИО:"), ("email", "E-mail:"), ("phone", "Телефон:"),
]
_SERVICE_KEYS = ("client_id", "client_type", "name", "phone", "email")
_DATE_FORMAT = "yyyy-MM-dd"


def _to_qdate(value: Any) -> QDate | None:
    """Преобразовать date/datetime/строку из БД в QDate."""
    if isinstance(value, (datetime, date)):
        return QDate(value.year, value.month, value.day)
    if value:
        parsed = QDate.fromString(str(value)[:10], _DATE_FORMAT)
        return parsed if parsed.isValid() else None
    return None


class _ClientFormDialog(BaseDialog):
    """Общая форма клиента: поля ЮЛ/ФЛ, блок пароля, кнопки.

    Подкласс создаёт заголовок (тип клиента) и передаёт его в ``_build_form``.
    """

    def __init__(self, parent: QWidget | None, title: str,
                 client_service: ClientService | None) -> None:
        super().__init__(parent, title=title, min_width=480)
        self.client_service = client_service or ClientService(_default_client_repo)
        self.ul_fields: dict[str, QLineEdit] = {}
        self.fl_fields: dict[str, QLineEdit | QDateEdit] = {}

    # ---------- построение ----------

    def _build_form(self, header: QHBoxLayout, password_label: str,
                    password_placeholder: str) -> None:
        self.root.addLayout(header)

        self.stacked = QStackedWidget()
        self.stacked.addWidget(self._build_ul_page())
        self.stacked.addWidget(self._build_fl_page())
        self.root.addWidget(self.stacked)

        self.root.addWidget(self._build_auth_group(password_label, password_placeholder))
        self.add_save_cancel_buttons(self._save)

    def _build_ul_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        for key, label in _UL_FIELDS:
            edit = QLineEdit()
            self.ul_fields[key] = edit
            form.addRow(label, edit)
        return page

    def _build_fl_page(self) -> QWidget:
        page = QWidget()
        form = QFormLayout(page)
        for key, label in _FL_TEXT_FIELDS:
            edit = QLineEdit()
            self.fl_fields[key] = edit
            form.addRow(label, edit)

        birth = QDateEdit()
        birth.setCalendarPopup(True)
        birth.setDisplayFormat(_DATE_FORMAT)
        self.fl_fields["birth_date"] = birth
        form.addRow("Дата рождения:", birth)

        series = QLineEdit()
        series.setMaxLength(4)
        self.fl_fields["passport_series"] = series
        form.addRow("Серия паспорта:", series)

        number = QLineEdit()
        number.setMaxLength(6)
        self.fl_fields["passport_number"] = number
        form.addRow("Номер паспорта:", number)
        return page

    def _build_auth_group(self, password_label: str, placeholder: str) -> QGroupBox:
        group = QGroupBox("Данные для входа клиента")
        form = QFormLayout(group)

        self.editPassword = QLineEdit()
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.editPassword.setPlaceholderText(placeholder)
        form.addRow(password_label, self.editPassword)

        btn_generate = QPushButton("🎲 Сгенерировать пароль")
        btn_generate.clicked.connect(self._generate_password)
        form.addRow("", btn_generate)

        form.addRow(QLabel("Вход осуществляется по E-mail или телефону"))
        return group

    # ---------- логика ----------

    def _generate_password(self) -> None:
        self.editPassword.setText(generate_password(8))
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)

    def _show_type_page(self, client_type: str) -> None:
        self.stacked.setCurrentIndex(0 if client_type == "ЮЛ" else 1)

    def _client_type(self) -> str:
        raise NotImplementedError

    def _collect(self) -> dict[str, Any]:
        """Собрать значения активной формы (ЮЛ или ФЛ) в словарь."""
        client_type = self._client_type()
        data: dict[str, Any] = {"client_type": client_type}
        fields = self.ul_fields if client_type == "ЮЛ" else self.fl_fields
        for key, widget in fields.items():
            if isinstance(widget, QDateEdit):
                data[key] = widget.date().toString(_DATE_FORMAT)
            else:
                data[key] = widget.text().strip()
        return data

    @staticmethod
    def _extra_fields(data: dict[str, Any]) -> dict[str, Any]:
        """Поля, не входящие в основные аргументы сервиса (адрес, ИНН, паспорт...)."""
        return {k: v for k, v in data.items() if k not in _SERVICE_KEYS}

    def _save(self) -> None:
        raise NotImplementedError


# ==================== ДОБАВЛЕНИЕ ====================
class ClientDialog(_ClientFormDialog):
    """Диалог добавления клиента."""

    def __init__(self, parent: QWidget | None, initial_type: str = "ЮЛ",
                 client_service: ClientService | None = None) -> None:
        super().__init__(parent, "Новый клиент", client_service)

        header = QHBoxLayout()
        header.addWidget(QLabel("Тип клиента:"))
        self.comboType = QComboBox()
        self.comboType.addItems(["ЮЛ", "ФЛ"])
        self.comboType.currentTextChanged.connect(self._show_type_page)
        header.addWidget(self.comboType)
        header.addStretch()

        self._build_form(header, "Пароль:", "Пароль для входа клиента")
        self.fl_fields["birth_date"].setDate(QDate.currentDate())
        if initial_type == "ФЛ":
            self.comboType.setCurrentText("ФЛ")

    def _client_type(self) -> str:
        return self.comboType.currentText()

    def _save(self) -> None:
        """Создать клиента. Валидацию выполняет ClientService."""
        data = self._collect()
        self.client_service.create_client(
            client_type=data["client_type"],
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            password=self.editPassword.text().strip(),
            **self._extra_fields(data),
        )
        self.info("Готово", "Клиент добавлен.")
        self.accept()


# ==================== РЕДАКТИРОВАНИЕ ====================
class ClientEditDialog(_ClientFormDialog):
    """Диалог редактирования клиента. Тип клиента изменить нельзя."""

    def __init__(self, parent: QWidget | None, client_id: int,
                 client_service: ClientService | None = None) -> None:
        super().__init__(parent, "Редактирование клиента", client_service)
        self.client_id = client_id
        self.client_data = self.client_service.get_client_details(client_id)

        header = QHBoxLayout()
        header.addWidget(QLabel("Тип клиента:"))
        header.addWidget(QLabel(self.client_data.get("client_type", "") if self.client_data else ""))
        header.addStretch()

        self._build_form(header, "Новый пароль:", "Оставьте пустым, чтобы не менять пароль")
        self._load_data()

    def _client_type(self) -> str:
        return self.client_data["client_type"]

    def _load_data(self) -> None:
        if not self.client_data:
            return
        client_type = self.client_data["client_type"]
        self._show_type_page(client_type)
        fields = self.ul_fields if client_type == "ЮЛ" else self.fl_fields
        for key, widget in fields.items():
            value = self.client_data.get(key)
            if isinstance(widget, QDateEdit):
                qdate = _to_qdate(value)
                if qdate:
                    widget.setDate(qdate)
            else:
                widget.setText(str(value or ""))

    def _save(self) -> None:
        """Обновить клиента. Пустой пароль означает «не менять»."""
        data = self._collect()
        password = self.editPassword.text().strip()
        self.client_service.update_client(
            client_id=self.client_id,
            client_type=data["client_type"],
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            password=password or None,
            **self._extra_fields(data),
        )
        self.info("Готово", "Клиент обновлён.")
        self.accept()


# ==================== ПРОСМОТР ====================
class ClientViewDialog(BaseDialog):
    """Диалог просмотра клиента (только чтение)."""

    def __init__(self, parent: QWidget | None, client_id: int,
                 client_service: ClientService | None = None) -> None:
        super().__init__(parent, title="Просмотр клиента", min_width=480)
        self.client_service = client_service or ClientService(_default_client_repo)
        self.client_data = self.client_service.get_client_details(client_id)

        info_box = QGroupBox("Информация о клиенте")
        self.form_lay = QFormLayout(info_box)
        self.root.addWidget(info_box)
        self.add_close_button()
        self._load_data()

    def _add_row(self, label: str, value: Any) -> None:
        self.form_lay.addRow(label, QLabel("" if value is None else str(value)))

    def _load_data(self) -> None:
        d = self.client_data
        if not d:
            return
        self._add_row("Тип:", d.get("client_type"))
        self._add_row("Название / ФИО:", d.get("name"))
        self._add_row("Телефон:", d.get("phone"))
        self._add_row("E-mail:", d.get("email"))
        if d["client_type"] == "ЮЛ":
            self._add_row("Адрес:", d.get("address"))
            self._add_row("ИНН:", d.get("inn"))
            self._add_row("КПП:", d.get("kpp"))
            self._add_row("Р/с:", d.get("bank_account"))
            self._add_row("БИК:", d.get("bik"))
            self._add_row("Руководитель:", d.get("director_name"))
            self._add_row("Контактное лицо:", d.get("contact_person"))
        else:
            self._add_row("Дата рождения:", d.get("birth_date"))
            passport = f"{d.get('passport_series') or ''} {d.get('passport_number') or ''}".strip()
            self._add_row("Паспорт:", passport)


__all__ = ["ClientDialog", "ClientEditDialog", "ClientViewDialog"]
