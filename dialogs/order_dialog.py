"""Диалог создания/редактирования заказа."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QWidget, QFormLayout
)
from db import order_repo, client_repo, services_repo
from session import Session


class OrderDialog(QDialog):
    """Диалог создания или редактирования заказа."""

    def __init__(self, parent, order_id=None):
        super().__init__(parent)
        self.order_id = order_id
        self.services = services_repo.get_all_services()
        self.service_checks: list[QCheckBox] = []
        self.setWindowTitle(
            "Новый заказ" if order_id is None else "Редактирование заказа"
        )
        self.setMinimumWidth(560)
        self._setup_ui()
        self._reload_clients()

        # При редактировании — загружаем данные, при создании — подставляем подсказку
        if self.order_id is not None:
            self._load_order()
        else:
            self._fill_suggested_code()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        # --- Код лабораторного сосуда ---
        code_box = QGroupBox("Код лабораторного сосуда")
        code_lay = QFormLayout(code_box)
        self.editVesselCode = QLineEdit()
        self.editVesselCode.setPlaceholderText("Например: С-0042")
        code_lay.addRow("Код сосуда:", self.editVesselCode)
        root.addWidget(code_box)

        # --- Заказчик ---
        client_box = QGroupBox("Заказчик")
        client_lay = QFormLayout(client_box)

        self.comboClientType = QComboBox()
        self.comboClientType.addItems(["ЮЛ", "ФЛ"])
        self.comboClientType.currentTextChanged.connect(self._reload_clients)
        client_lay.addRow("Тип заказчика:", self.comboClientType)

        self.comboClient = QComboBox()
        client_lay.addRow("Клиент:", self.comboClient)

        btn_row = QHBoxLayout()
        self.btnNewClient = QPushButton("+ Добавить нового клиента")
        self.btnNewClient.clicked.connect(self._open_new_client_dialog)
        btn_row.addWidget(self.btnNewClient)

        self.btnRefreshServices = QPushButton("🔄 Обновить услуги")
        self.btnRefreshServices.clicked.connect(self._reload_services)
        btn_row.addWidget(self.btnRefreshServices)

        btn_row.addStretch()
        client_lay.addRow(btn_row)
        root.addWidget(client_box)

        # --- Услуги ---
        services_box = QGroupBox("Исследования / услуги")
        services_lay = QVBoxLayout(services_box)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        self.services_layout = QVBoxLayout(scroll_widget)
        self._build_services_list()
        scroll.setWidget(scroll_widget)
        services_lay.addWidget(scroll)
        root.addWidget(services_box)

        # --- Итого ---
        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("Итого:"))
        self.lblTotal = QLabel("0.00 ₽")
        self.lblTotal.setStyleSheet(
            "font-size: 14pt; font-weight: bold; color: #174A7E;"
        )
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        root.addLayout(total_lay)

        # --- Кнопки ---
        btns = QHBoxLayout()
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(self._save)
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_save)
        btns.addWidget(btn_cancel)
        root.addLayout(btns)

    def _build_services_list(self):
        """Построить список чекбоксов услуг из self.services."""
        # Удаляем старые чекбоксы (кроме stretch в конце)
        while self.services_layout.count() > 1:
            item = self.services_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.service_checks.clear()

        if not self.services:
            empty_label = QLabel("Нет доступных услуг. Добавьте их через «Услуги».")
            empty_label.setStyleSheet("color: gray; font-style: italic;")
            self.services_layout.addWidget(empty_label)
            return

        for s in self.services:
            cb = QCheckBox(f"{s['service_name']}  —  {float(s['price']):.2f} ₽")
            cb.service_id = s['service_id']
            cb.price = float(s['price'])
            cb.stateChanged.connect(self._recalc_total)
            self.service_checks.append(cb)
            self.services_layout.addWidget(cb)
        self.services_layout.addStretch()

    def _reload_services(self):
        """Перезагрузить список услуг из БД (если админ добавил новые)."""
        self.services = services_repo.get_all_services()
        self._build_services_list()

    def _fill_suggested_code(self):
        """Подставить следующий свободный код сосуда."""
        suggested = order_repo.get_next_vessel_code()
        self.editVesselCode.setText(suggested)
        self.editVesselCode.selectAll()

    def _reload_clients(self):
        """Перезагрузить список клиентов под выбранный тип."""
        ctype = self.comboClientType.currentText()
        clients = client_repo.get_clients_by_type(ctype)
        self.comboClient.clear()
        for c in clients:
            display = (
                f"{c['name']} ({c['contact_person']})"
                if c.get('contact_person')
                else c['name']
            )
            self.comboClient.addItem(display, c['client_id'])

    def _open_new_client_dialog(self):
        from dialogs.client_dialog import ClientDialog
        dlg = ClientDialog(self, initial_type=self.comboClientType.currentText())
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._reload_clients()
            if self.comboClient.count() > 0:
                self.comboClient.setCurrentIndex(self.comboClient.count() - 1)

    def _recalc_total(self):
        """Пересчитать итоговую сумму."""
        total = sum(cb.price for cb in self.service_checks if cb.isChecked())
        self.lblTotal.setText(f"{total:.2f} ₽")

    def _load_order(self):
        """Загрузить данные существующего заказа в форму."""
        order = order_repo.get_order(self.order_id)
        if not order:
            return

        # Код сосуда
        self.editVesselCode.setText(order['vessel_code'])

        # Тип клиента (устанавливаем ДО загрузки списка)
        client_type = order.get('client_type', 'ЮЛ')
        self.comboClientType.setCurrentText(client_type)

        # Перезагружаем клиентов под выбранный тип и выбираем нужного
        self._reload_clients()
        for i in range(self.comboClient.count()):
            if self.comboClient.itemData(i) == order['client_id']:
                self.comboClient.setCurrentIndex(i)
                break

        # Загружаем услуги — отмечаем нужные чекбоксы
        services = order_repo.get_order_services(self.order_id)
        service_ids = [s['service_id'] for s in services]
        for cb in self.service_checks:
            cb.setChecked(cb.service_id in service_ids)

        self._recalc_total()

    def _validate_vessel_code(self, code: str) -> str | None:
        """Проверка уникальности кода сосуда."""
        if not code.strip():
            return "Введите код сосуда."
        # При редактировании исключаем текущий заказ из проверки
        if order_repo.vessel_code_exists(
            code.strip(),
            exclude_archived=True,
            exclude_order_id=self.order_id,
        ):
            return (
                f"Код «{code}» уже используется в активных заказах.\n"
                "Введите другой или используйте предложенный."
            )
        return None

    def _save(self):
        """Сохранить заказ (создать или обновить)."""
        code = self.editVesselCode.text().strip()
        err = self._validate_vessel_code(code)
        if err:
            QMessageBox.warning(self, "Ошибка", err)
            return

        if self.comboClient.count() == 0:
            QMessageBox.warning(
                self, "Ошибка", "Выберите клиента или добавьте нового."
            )
            return
        client_id = self.comboClient.currentData()

        selected = [cb.service_id for cb in self.service_checks if cb.isChecked()]
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну услугу.")
            return

        total = sum(cb.price for cb in self.service_checks if cb.isChecked())
        employee_id = Session.get_user_id()

        try:
            if self.order_id is None:
                # Создание нового заказа
                order_repo.create_order(
                    vessel_code=code,
                    client_id=client_id,
                    employee_id=employee_id,
                    service_ids=selected,
                    total_price=total,
                )
                QMessageBox.information(self, "Готово", "Заказ успешно создан.")
            else:
                # Обновление существующего заказа
                order_repo.update_order(
                    order_id=self.order_id,
                    vessel_code=code,
                    client_id=client_id,
                    employee_id=employee_id,
                    service_ids=selected,
                    total_price=total,
                )
                QMessageBox.information(self, "Готово", "Заказ успешно обновлён.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось сохранить заказ:\n{e}"
            )