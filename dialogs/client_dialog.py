"""Диалоги клиентов: добавление, редактирование, просмотр."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QMessageBox, QFormLayout,
    QDateEdit, QStackedWidget, QWidget, QGroupBox
)
from PyQt6.QtCore import QDate
from db import client_repo


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
        try:
            client_repo.add_client(data)
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

        btns = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

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
        try:
            client_repo.update_client(data)
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