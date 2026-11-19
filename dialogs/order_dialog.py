"""Диалог создания/редактирования заказа."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QCheckBox, QPushButton, QMessageBox, QGroupBox,
    QScrollArea, QWidget, QFormLayout
)
from PyQt6.QtCore import Qt
from db import order_repo, client_repo, services_repo
from session import Session


class OrderDialog(QDialog):
    """Диалог создания или редактирования заказа."""

    def __init__(self, parent, order_id=None):
        super().__init__(parent)
        self.order_id = order_id
        self.all_services = services_repo.get_all_services()  # все услуги для поиска
        self.service_checks: list[QCheckBox] = []  # видимые чекбоксы
        self.setWindowTitle(
            "Новый заказ" if order_id is None else "Редактирование заказа"
        )
        self.setMinimumWidth(560)
        self.setMinimumHeight(600)
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

        # --- Услуги с поиском ---
        services_box = QGroupBox("Исследования / услуги")
        services_lay = QVBoxLayout(services_box)

        # Поле поиска
        search_lay = QHBoxLayout()
        search_lay.addWidget(QLabel("🔍 Поиск:"))
        self.editServiceSearch = QLineEdit()
        self.editServiceSearch.setPlaceholderText("Введите название услуги...")
        self.editServiceSearch.textChanged.connect(self._filter_services)
        search_lay.addWidget(self.editServiceSearch)
        services_lay.addLayout(search_lay)

        # Счётчик отображаемых услуг
        self.lblServiceCount = QLabel("0 из 0")
        self.lblServiceCount.setStyleSheet("color: #666; font-size: 9pt;")
        self.lblServiceCount.setAlignment(Qt.AlignmentFlag.AlignRight)
        services_lay.addWidget(self.lblServiceCount)

        # ScrollArea с фиксированной высотой
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        scroll.setMaximumHeight(300)  # фиксируем максимальную высоту
        scroll.setStyleSheet("""
            QScrollArea {
                border: 1px solid #CBD7E4;
                border-radius: 4px;
                background-color: #FAFBFC;
            }
        """)

        scroll_widget = QWidget()
        self.services_layout = QVBoxLayout(scroll_widget)
        self.services_layout.setContentsMargins(8, 8, 8, 8)
        self.services_layout.setSpacing(4)

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
        """Построить список чекбоксов услуг из self.all_services."""
        # Удаляем старые чекбоксы
        while self.services_layout.count() > 0:
            item = self.services_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.service_checks.clear()

        if not self.all_services:
            empty_label = QLabel("Нет доступных услуг. Добавьте их через «Услуги».")
            empty_label.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
            self.services_layout.addWidget(empty_label)
            self._update_service_count(0, 0)
            return

        for s in self.all_services:
            cb = QCheckBox(f"{s['service_name']}  —  {float(s['price']):.2f} ₽")
            cb.service_id = s['service_id']
            cb.price = float(s['price'])
            cb.stateChanged.connect(self._recalc_total)
            # Фиксируем минимальную высоту чекбокса, чтобы не сжимались
            cb.setMinimumHeight(28)
            self.service_checks.append(cb)
            self.services_layout.addWidget(cb)

        self.services_layout.addStretch()
        self._update_service_count(len(self.service_checks), len(self.all_services))

    def _filter_services(self):
        """Фильтрация услуг по введённому тексту."""
        query = self.editServiceSearch.text().strip().lower()
        visible_count = 0

        for cb in self.service_checks:
            if not query or query in cb.text().lower():
                cb.setVisible(True)
                visible_count += 1
            else:
                cb.setVisible(False)

        self._update_service_count(visible_count, len(self.all_services))

    def _update_service_count(self, visible: int, total: int):
        """Обновить счётчик отображаемых услуг."""
        if total == 0:
            self.lblServiceCount.setText("Нет услуг")
        elif visible == total:
            self.lblServiceCount.setText(f"Всего: {total}")
        else:
            self.lblServiceCount.setText(f"Найдено: {visible} из {total}")

    def _reload_services(self):
        """Перезагрузить список услуг из БД."""
        self.all_services = services_repo.get_all_services()
        self.editServiceSearch.clear()
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
        total = sum(cb.price for cb in self.service_checks if cb.isChecked() and cb.isVisible())
        self.lblTotal.setText(f"{total:.2f} ₽")

    def _load_order(self):
        """Загрузить данные существующего заказа в форму."""
        order = order_repo.get_order(self.order_id)
        if not order:
            return

        # Код сосуда
        self.editVesselCode.setText(order['vessel_code'])

        # Тип клиента
        client_type = order.get('client_type', 'ЮЛ')
        self.comboClientType.setCurrentText(client_type)

        # Перезагружаем клиентов и выбираем нужного
        self._reload_clients()
        for i in range(self.comboClient.count()):
            if self.comboClient.itemData(i) == order['client_id']:
                self.comboClient.setCurrentIndex(i)
                break

        # Загружаем услуги
        services = order_repo.get_order_services(self.order_id)
        service_ids = [s['service_id'] for s in services]
        for cb in self.service_checks:
            cb.setChecked(cb.service_id in service_ids)

        self._recalc_total()

    def _validate_vessel_code(self, code: str) -> str | None:
        """Проверка уникальности кода сосуда."""
        if not code.strip():
            return "Введите код сосуда."
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
        """Сохранить заказ."""
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

        # Берём только видимые и отмеченные услуги
        selected = [
            cb.service_id
            for cb in self.service_checks
            if cb.isChecked() and cb.isVisible()
        ]
        if not selected:
            QMessageBox.warning(self, "Ошибка", "Выберите хотя бы одну услугу.")
            return

        total = sum(
            cb.price for cb in self.service_checks if cb.isChecked() and cb.isVisible()
        )
        employee_id = Session.get_user_id()

        try:
            if self.order_id is None:
                order_repo.create_order(
                    vessel_code=code,
                    client_id=client_id,
                    employee_id=employee_id,
                    service_ids=selected,
                    total_price=total,
                )
                QMessageBox.information(self, "Готово", "Заказ успешно создан.")
            else:
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