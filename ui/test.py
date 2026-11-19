"""Тестовый диалог добавления клиента. Запускается независимо от основного приложения."""
import sys
from PyQt6.QtWidgets import (
    QApplication, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QPushButton, QFormLayout, QDateEdit, QStackedWidget, QWidget
)
from PyQt6.QtCore import QDate


class ClientDialog(QDialog):
    """Диалог добавления клиента с QStackedWidget."""
    
    def __init__(self, parent=None, initial_type: str = "ЮЛ"):
        super().__init__(parent)
        self.setWindowTitle("Новый клиент (ТЕСТ)")
        self.setMinimumWidth(480)
        self._build_ui()
        if initial_type == "ФЛ":
            self.comboType.setCurrentText("ФЛ")

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Выбор типа клиента
        type_lay = QHBoxLayout()
        type_lay.addWidget(QLabel("Тип клиента:"))
        self.comboType = QComboBox()
        self.comboType.addItems(["ЮЛ", "ФЛ"])
        self.comboType.currentTextChanged.connect(self._on_type_changed)
        type_lay.addWidget(self.comboType)
        type_lay.addStretch()
        root.addLayout(type_lay)

        # QStackedWidget: две формы
        self.stacked = QStackedWidget()

        # Форма ЮЛ
        ul_widget = QWidget()
        ul_form = QFormLayout(ul_widget)
        self.ul_fields = {}
        for key, label in [
            ("name", "Название компании:"),
            ("address", "Адрес:"),
            ("inn", "ИНН:"),
            ("kpp", "КПП:"),
            ("bank_account", "Расчётный счёт:"),
            ("bik", "БИК:"),
            ("director_name", "ФИО руководителя:"),
            ("contact_person", "ФИО контактного лица:"),
            ("phone", "Телефон:"),
            ("email", "E-mail:"),
        ]:
            le = QLineEdit()
            self.ul_fields[key] = le
            ul_form.addRow(label, le)
        self.stacked.addWidget(ul_widget)

        # Форма ФЛ
        fl_widget = QWidget()
        fl_form = QFormLayout(fl_widget)
        self.fl_fields = {}
        for key, label in [
            ("name", "ФИО:"),
            ("email", "E-mail:"),
            ("phone", "Телефон:"),
        ]:
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
        """Переключение между формами."""
        if ctype == "ЮЛ":
            self.stacked.setCurrentIndex(0)
        else:
            self.stacked.setCurrentIndex(1)

    def _collect(self) -> dict:
        """Собирает данные из активной формы."""
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
        print("Собранные данные:", data)
        self.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = ClientDialog()
    if dlg.exec() == QDialog.DialogCode.Accepted:
        print("Диалог завершён успешно")
    sys.exit(0)