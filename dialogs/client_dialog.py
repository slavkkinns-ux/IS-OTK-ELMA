"""Диалоги клиентов: добавление, редактирование, просмотр."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFormLayout,
    QDateEdit, QStackedWidget, QWidget, QGroupBox
)
from PyQt6.QtCore import QDate
from db import client_repo
import hashlib
import random
import string


# ==================== ДОБАВЛЕНИЕ ====================
class ClientDialog(QDialog):
    def __init__(self, parent, initial_type: str = "ЮЛ"):
        super().__init__(parent)
        self.setWindowTitle("Новый клиент")
        self.setMinimumWidth(480)
        self._build_ui()
        if initial_type == "ФЛ":
            self.comboType.setCurrentText("ФЛ")

    def _build_ui(self):
        root = QVBoxLayout(self)

        type_lay = QHBoxLayout()
        type_lay.addWidget(QLabel("Тип клиента:"))
        self.comboType = QComboBox()
        self.comboType.addItems(["ЮЛ", "ФЛ"])
        self.comboType.currentTextChanged.connect(self._on_type_changed)
        type_lay.addWidget(self.comboType)
        type_lay.addStretch()
        root.addLayout(type_lay)

        self.stacked = QStackedWidget()

        # ЮЛ
        ul_widget = QWidget()
        ul_form = QFormLayout(ul_widget)
        self.ul_fields = {}
        for key, label in [
            ("name", "Название компании:"), ("address", "Адрес:"), ("inn", "ИНН:"),
            ("kpp", "КПП:"), ("bank_account", "Расчётный счёт:"), ("bik", "БИК:"),
            ("director_name", "ФИО руководителя:"), ("contact_person", "ФИО контактного лица:"),
            ("phone", "Телефон:"), ("email", "E-mail:"),
        ]:
            le = QLineEdit()
            self.ul_fields[key] = le
            ul_form.addRow(label, le)
        self.stacked.addWidget(ul_widget)

        # ФЛ
        fl_widget = QWidget()
        fl_form = QFormLayout(fl_widget)
        self.fl_fields = {}
        for key, label in [("name", "ФИО:"), ("email", "E-mail:"), ("phone", "Телефон:")]:
            le = QLineEdit()
            self.fl_fields[key] = le
            fl_form.addRow(label, le)
        self.fl_fields["birth_date"] = QDateEdit()
        self.fl_fields["birth_date"].setCalendarPopup(True)
        self.fl_fields["birth_date"].setDisplayFormat("yyyy-MM-dd")
        self.fl_fields["birth_date"].setDate(QDate.currentDate())
        fl_form.addRow("Дата рождения:", self.fl_fields["birth_date"])
        self.fl_fields["passport_series"] = QLineEdit()
        self.fl_fields["passport_series"].setMaxLength(4)
        fl_form.addRow("Серия паспорта:", self.fl_fields["passport_series"])
        self.fl_fields["passport_number"] = QLineEdit()
        self.fl_fields["passport_number"].setMaxLength(6)
        fl_form.addRow("Номер паспорта:", self.fl_fields["passport_number"])
        self.stacked.addWidget(fl_widget)

        root.addWidget(self.stacked)

        # Поля логина и пароля (общие для обоих типов)
        auth_group = QGroupBox("Данные для входа клиента")
        auth_form = QFormLayout(auth_group)

        self.editLogin = QLineEdit()
        self.editLogin.setPlaceholderText("Email или телефон для входа")
        auth_form.addRow("Логин:", self.editLogin)

        self.editPassword = QLineEdit()
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.editPassword.setPlaceholderText("Пароль для входа")
        auth_form.addRow("Пароль:", self.editPassword)

        btn_generate = QPushButton("🎲 Сгенерировать пароль")
        btn_generate.clicked.connect(self._generate_password)
        auth_form.addRow("", btn_generate)

        root.addWidget(auth_group)

        # Кнопки
        btns = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

    def _on_type_changed(self, ctype: str):
        if ctype == "ЮЛ":
            self.stacked.setCurrentIndex(0)
        else:
            self.stacked.setCurrentIndex(1)

    def _generate_password(self):
        """Сгенерировать случайный пароль из 8 символов."""
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choices(chars, k=8))
        self.editPassword.setText(password)
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)

    def _collect(self) -> dict:
        ctype = self.comboType.currentText()
        data = {"client_type": ctype}
        if ctype == "ЮЛ":
            for k, w in self.ul_fields.items():
                data[k] = w.text().strip()
        else:
            for k, w in self.fl_fields.items():
                if isinstance(w, QDateEdit):
                    data[k] = w.date().toString("yyyy-MM-dd")
                else:
                    data[k] = w.text().strip()
        return data

    def _save(self):
        data = self._collect()
        if not data.get("name"):
            QMessageBox.warning(self, "Ошибка", "Укажите название / ФИО.")
            return

        login = self.editLogin.text().strip()
        password = self.editPassword.text().strip()

        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин для входа клиента.")
            return
        if not password:
            QMessageBox.warning(self, "Ошибка", "Введите пароль для входа клиента.")
            return

        # Проверка уникальности логина
        if client_repo.client_login_exists(login):
            QMessageBox.warning(self, "Ошибка", f"Логин «{login}» уже используется.")
            return

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            client_repo.create_client(
                client_type=data["client_type"],
                name=data["name"],
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                login=login,
                password_hash=password_hash,
                **{k: v for k, v in data.items() if k not in ("client_type", "name", "phone", "email")}
            )
            QMessageBox.information(self, "Готово", "Клиент добавлен.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")


# ==================== РЕДАКТИРОВАНИЕ ====================
class ClientEditDialog(QDialog):
    def __init__(self, parent, client_id: int):
        super().__init__(parent)
        self.client_id = client_id
        self.client_data = client_repo.get_client_details(client_id)
        self.setWindowTitle("Редактирование клиента")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)

        type_lay = QHBoxLayout()
        type_lay.addWidget(QLabel("Тип клиента:"))
        self.lblType = QLabel(self.client_data.get('client_type', '') if self.client_data else '')
        type_lay.addWidget(self.lblType)
        type_lay.addStretch()
        root.addLayout(type_lay)

        self.stacked = QStackedWidget()

        ul_widget = QWidget()
        ul_form = QFormLayout(ul_widget)
        self.ul_fields = {}
        for key, label in [("name", "Название компании:"), ("address", "Адрес:"), ("inn", "ИНН:"),
                           ("kpp", "КПП:"), ("bank_account", "Расчётный счёт:"), ("bik", "БИК:"),
                           ("director_name", "ФИО руководителя:"), ("contact_person", "ФИО контактного лица:"),
                           ("phone", "Телефон:"), ("email", "E-mail:")]:
            le = QLineEdit()
            self.ul_fields[key] = le
            ul_form.addRow(label, le)
        self.stacked.addWidget(ul_widget)

        fl_widget = QWidget()
        fl_form = QFormLayout(fl_widget)
        self.fl_fields = {}
        for key, label in [("name", "ФИО:"), ("email", "E-mail:"), ("phone", "Телефон:")]:
            le = QLineEdit()
            self.fl_fields[key] = le
            fl_form.addRow(label, le)
        self.fl_fields["birth_date"] = QDateEdit()
        self.fl_fields["birth_date"].setCalendarPopup(True)
        self.fl_fields["birth_date"].setDisplayFormat("yyyy-MM-dd")
        fl_form.addRow("Дата рождения:", self.fl_fields["birth_date"])
        self.fl_fields["passport_series"] = QLineEdit()
        self.fl_fields["passport_series"].setMaxLength(4)
        fl_form.addRow("Серия паспорта:", self.fl_fields["passport_series"])
        self.fl_fields["passport_number"] = QLineEdit()
        self.fl_fields["passport_number"].setMaxLength(6)
        fl_form.addRow("Номер паспорта:", self.fl_fields["passport_number"])
        self.stacked.addWidget(fl_widget)

        root.addWidget(self.stacked)

        # Поля логина и пароля
        auth_group = QGroupBox("Данные для входа клиента")
        auth_form = QFormLayout(auth_group)

        self.editLogin = QLineEdit()
        self.editLogin.setPlaceholderText("Email или телефон для входа")
        auth_form.addRow("Логин:", self.editLogin)

        self.editPassword = QLineEdit()
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.editPassword.setPlaceholderText("Оставьте пустым, чтобы не менять пароль")
        auth_form.addRow("Новый пароль:", self.editPassword)

        btn_generate = QPushButton("🎲 Сгенерировать пароль")
        btn_generate.clicked.connect(self._generate_password)
        auth_form.addRow("", btn_generate)

        root.addWidget(auth_group)

        btns = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

    def _generate_password(self):
        chars = string.ascii_letters + string.digits
        password = ''.join(random.choices(chars, k=8))
        self.editPassword.setText(password)
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Normal)

    def _load_data(self):
        if not self.client_data:
            return
        if self.client_data['client_type'] == 'ЮЛ':
            self.stacked.setCurrentIndex(0)
            for k, w in self.ul_fields.items():
                if isinstance(w, QLineEdit):
                    w.setText(str(self.client_data.get(k, '') or ''))
        else:
            self.stacked.setCurrentIndex(1)
            for k, w in self.fl_fields.items():
                if isinstance(w, QLineEdit):
                    w.setText(str(self.client_data.get(k, '') or ''))
                elif isinstance(w, QDateEdit) and self.client_data.get('birth_date'):
                    w.setDate(self.client_data['birth_date'])

        # Загружаем логин (если есть)
        self.editLogin.setText(str(self.client_data.get('login', '') or ''))

    def _collect(self) -> dict:
        ctype = self.client_data['client_type']
        data = {"client_id": self.client_id, "client_type": ctype}
        if ctype == "ЮЛ":
            for k, w in self.ul_fields.items():
                data[k] = w.text().strip()
        else:
            for k, w in self.fl_fields.items():
                if isinstance(w, QDateEdit):
                    data[k] = w.date().toString("yyyy-MM-dd")
                else:
                    data[k] = w.text().strip()
        return data

    def _save(self):
        data = self._collect()
        if not data.get("name"):
            QMessageBox.warning(self, "Ошибка", "Укажите название / ФИО.")
            return

        login = self.editLogin.text().strip()
        password = self.editPassword.text().strip()

        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин для входа клиента.")
            return

        # Проверка уникальности логина (исключая текущего клиента)
        if client_repo.client_login_exists(login, exclude_id=self.client_id):
            QMessageBox.warning(self, "Ошибка", f"Логин «{login}» уже используется.")
            return

        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        try:
            client_repo.update_client(
                client_id=self.client_id,
                client_type=data["client_type"],
                name=data["name"],
                phone=data.get("phone", ""),
                email=data.get("email", ""),
                login=login,
                password_hash=password_hash,
                **{k: v for k, v in data.items() if k not in ("client_id", "client_type", "name", "phone", "email")}
            )
            QMessageBox.information(self, "Готово", "Клиент обновлён.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")


# ==================== ПРОСМОТР ====================
class ClientViewDialog(QDialog):
    def __init__(self, parent, client_id: int):
        super().__init__(parent)
        self.client_data = client_repo.get_client_details(client_id)
        self.setWindowTitle("Просмотр клиента")
        self.setMinimumWidth(480)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)
        info_box = QGroupBox("Информация о клиенте")
        self.form_lay = QFormLayout(info_box)
        root.addWidget(info_box)
        btns = QHBoxLayout()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load_data(self):
        if not self.client_data:
            return
        d = self.client_data
        self.form_lay.addRow("Тип:", QLabel(d.get('client_type', '')))
        self.form_lay.addRow("Название / ФИО:", QLabel(d.get('name', '')))
        self.form_lay.addRow("Телефон:", QLabel(d.get('phone', '')))
        self.form_lay.addRow("E-mail:", QLabel(d.get('email', '')))
        self.form_lay.addRow("Логин:", QLabel(d.get('login', '—')))
        if d['client_type'] == 'ЮЛ':
            self.form_lay.addRow("Адрес:", QLabel(d.get('address', '')))
            self.form_lay.addRow("ИНН:", QLabel(d.get('inn', '')))
            self.form_lay.addRow("КПП:", QLabel(d.get('kpp', '')))
            self.form_lay.addRow("Р/с:", QLabel(d.get('bank_account', '')))
            self.form_lay.addRow("БИК:", QLabel(d.get('bik', '')))
            self.form_lay.addRow("Руководитель:", QLabel(d.get('director_name', '')))
            self.form_lay.addRow("Контактное лицо:", QLabel(d.get('contact_person', '')))
        else:
            self.form_lay.addRow("Дата рождения:", QLabel(str(d.get('birth_date', ''))))
            self.form_lay.addRow("Паспорт:", QLabel(f"{d.get('passport_series', '')} {d.get('passport_number', '')}".strip()))