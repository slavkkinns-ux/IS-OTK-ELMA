"""Диалог управления услугами."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QMessageBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QGroupBox
)
from PyQt6.QtCore import Qt
from db import services_repo


class ServicesDialog(QDialog):
    """Диалог управления списком услуг (CRUD)."""

    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("Управление услугами")
        self.setMinimumWidth(700)
        self.setMinimumHeight(500)
        self._build_ui()
        self._load_services()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Заголовок
        title = QLabel("Список услуг")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #174A7E; padding: 5px;")
        root.addWidget(title)

        # Таблица услуг
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "Название услуги", "Цена, ₽", "Статус"])
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setStyleSheet("""
            QHeaderView::section {
                background-color: #174A7E; color: white; font-weight: bold;
                padding: 5px; border: 1px solid #CBD7E4;
            }
            QTableWidget {
                border: 1px solid #CBD7E4; gridline-color: #CBD7E4;
            }
        """)
        root.addWidget(self.table)

        # Кнопки управления
        btns = QHBoxLayout()
        btn_add = QPushButton("+ Добавить")
        btn_add.clicked.connect(self._add_service)
        btn_edit = QPushButton("✎ Редактировать")
        btn_edit.clicked.connect(self._edit_service)
        btn_toggle = QPushButton("Включить/Отключить")
        btn_toggle.clicked.connect(self._toggle_service)
        btn_delete = QPushButton("✕ Удалить")
        btn_delete.clicked.connect(self._delete_service)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)

        btns.addWidget(btn_add)
        btns.addWidget(btn_edit)
        btns.addWidget(btn_toggle)
        btns.addWidget(btn_delete)
        btns.addStretch()
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load_services(self):
        """Загрузить все услуги (включая отключённые) в таблицу."""
        services = services_repo.get_all_services(include_inactive=True)
        self.table.setRowCount(0)
        if not services:
            return
        self.table.setRowCount(len(services))
        for row_idx, s in enumerate(services):
            item_id = QTableWidgetItem(str(s['service_id']))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row_idx, 0, item_id)

            item_name = QTableWidgetItem(s['service_name'])
            self.table.setItem(row_idx, 1, item_name)

            item_price = QTableWidgetItem(f"{float(s['price']):.2f}")
            item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.table.setItem(row_idx, 2, item_price)

            status = "Активна" if s['is_active'] else "Отключена"
            item_status = QTableWidgetItem(status)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if not s['is_active']:
                item_status.setForeground(Qt.GlobalColor.gray)
                item_name.setForeground(Qt.GlobalColor.gray)
            self.table.setItem(row_idx, 3, item_status)

    def _get_selected_service(self):
        """Получить данные выбранной строки."""
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            'service_id': int(self.table.item(row, 0).text()),
            'service_name': self.table.item(row, 1).text(),
            'price': float(self.table.item(row, 2).text()),
            'is_active': self.table.item(row, 3).text() == "Активна",
        }

    def _add_service(self):
        """Открыть диалог добавления услуги."""
        dlg = ServiceEditDialog(self, service=None)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_services()

    def _edit_service(self):
        """Открыть диалог редактирования выбранной услуги."""
        service = self._get_selected_service()
        if not service:
            QMessageBox.information(self, "Редактирование", "Выберите услугу в таблице.")
            return
        dlg = ServiceEditDialog(self, service=service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_services()

    def _toggle_service(self):
        """Включить/отключить выбранную услугу."""
        service = self._get_selected_service()
        if not service:
            QMessageBox.information(self, "Статус", "Выберите услугу в таблице.")
            return
        new_status = 0 if service['is_active'] else 1
        action = "отключить" if service['is_active'] else "включить"

        # Кастомный диалог с русским текстом
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle("Подтверждение")
        msg.setText(f"Вы уверены, что хотите {action} услугу «{service['service_name']}»?")
        btn_yes = msg.addButton("Да", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(btn_no)
        msg.exec()

        if msg.clickedButton() == btn_yes:
            services_repo.update_service(
                service['service_id'], service['service_name'],
                service['price'], new_status
            )
            self._load_services()

    def _delete_service(self):
        service = self._get_selected_service()
        if not service:
            QMessageBox.information(self, "Удаление", "Выберите услугу в таблице.")
            return

        # Проверка использования
        if services_repo.is_service_used(service['service_id']):
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Удаление услуги")
            msg.setText(
                f"Услуга «{service['service_name']}» используется в существующих заказах.\n"
                f"Удаление может нарушить целостность данных.\n\n"
                f"Продолжить?"
            )
            btn_yes = msg.addButton("Да, удалить", QMessageBox.ButtonRole.YesRole)
            btn_no = msg.addButton("Отмена", QMessageBox.ButtonRole.NoRole)
            msg.setDefaultButton(btn_no)
            msg.exec()
            if msg.clickedButton() != btn_yes:
                return

        # Диалог подтверждения
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Удаление услуги")
        msg.setText(f"Услуга «{service['service_name']}» будет удалена безвозвратно.\n\nПродолжить?")
        btn_yes = msg.addButton("Да", QMessageBox.ButtonRole.YesRole)
        btn_no = msg.addButton("Нет", QMessageBox.ButtonRole.NoRole)
        msg.setDefaultButton(btn_no)
        msg.exec()

        if msg.clickedButton() == btn_yes:
            try:
                services_repo.delete_service(service['service_id'], soft=False)
                self._load_services()
                QMessageBox.information(self, "Готово", "Услуга удалена.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось удалить услугу:\n{e}")


class ServiceEditDialog(QDialog):
    """Диалог добавления/редактирования услуги."""

    def __init__(self, parent, service: dict | None):
        super().__init__(parent)
        self.service = service
        self.setWindowTitle("Новая услуга" if service is None else "Редактирование услуги")
        self.setMinimumWidth(400)
        self._build_ui()
        if service:
            self.editName.setText(service['service_name'])
            self.editPrice.setText(f"{float(service['price']):.2f}")

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Название
        name_lay = QHBoxLayout()
        name_lay.addWidget(QLabel("Название услуги:"))
        self.editName = QLineEdit()
        self.editName.setPlaceholderText("Например: Химический анализ")
        name_lay.addWidget(self.editName)
        root.addLayout(name_lay)

        # Цена
        price_lay = QHBoxLayout()
        price_lay.addWidget(QLabel("Цена (₽):"))
        self.editPrice = QLineEdit()
        self.editPrice.setPlaceholderText("0.00")
        price_lay.addWidget(self.editPrice)
        root.addLayout(price_lay)

        # Кнопки
        btns = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

    def _validate(self) -> str | None:
        name = self.editName.text().strip()
        price_text = self.editPrice.text().strip()

        if not name:
            return "Введите название услуги."
        if len(name) < 3:
            return "Название должно содержать минимум 3 символа."

        # Проверка дубликата
        exclude_id = self.service['service_id'] if self.service else None
        if services_repo.service_name_exists(name, exclude_id=exclude_id):
            return f"Услуга с названием «{name}» уже существует."

        if not price_text:
            return "Введите цену."
        try:
            price = float(price_text.replace(',', '.'))
            if price < 0:
                return "Цена не может быть отрицательной."
        except ValueError:
            return "Некорректный формат цены."

        return None

    def _save(self):
        err = self._validate()
        if err:
            QMessageBox.warning(self, "Ошибка", err)
            return

        name = self.editName.text().strip()
        price = float(self.editPrice.text().strip().replace(',', '.'))

        try:
            if self.service is None:
                services_repo.add_service(name, price)
                QMessageBox.information(self, "Готово", "Услуга добавлена.")
            else:
                services_repo.update_service(
                    self.service['service_id'], name, price,
                    1 if self.service['is_active'] else 0
                )
                QMessageBox.information(self, "Готово", "Услуга обновлена.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")