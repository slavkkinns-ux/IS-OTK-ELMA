from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QPushButton, QMessageBox, QHeaderView, QGroupBox, QLabel,
    QDoubleSpinBox, QAbstractItemView
)
from PyQt6.QtCore import Qt
from db import client_repo, order_repo
from session import Session


class OrderDialog(QDialog):
    """Единый диалог для создания и редактирования заказа."""

    def __init__(self, parent=None, order_id: int = None):
        super().__init__(parent)
        self.order_id = order_id          # None = создание, иначе — редактирование
        self.is_edit = order_id is not None
        self.services_cache = []          # кэш справочника услуг
        self.setWindowTitle(
            "Редактирование заказа" if self.is_edit else "Новый заказ"
        )
        self.setMinimumSize(720, 560)
        self._build_ui()
        self._load_references()
        if self.is_edit:
            self._load_order()

    # --------------------- UI ---------------------
    def _build_ui(self):
        root = QVBoxLayout(self)

        # --- Блок основных полей ---
        grp_main = QGroupBox("Основные данные")
        form = QFormLayout(grp_main)

        self.edt_vessel = QLineEdit()
        self.edt_vessel.setPlaceholderText("Например: VSL-00123")
        form.addRow("Код судна *:", self.edt_vessel)

        self.cmb_client = QComboBox()
        self.cmb_client.setEditable(False)
        form.addRow("Клиент *:", self.cmb_client)

        self.cmb_status = QComboBox()
        self.cmb_status.addItems(["Новый", "В работе", "Ожидает проверки", "Завершён", "Отменён"])
        form.addRow("Статус:", self.cmb_status)

        self.lbl_employee = QLabel(Session.get_display_name())
        form.addRow("Сотрудник:", self.lbl_employee)

        root.addWidget(grp_main)

        # --- Блок услуг ---
        grp_services = QGroupBox("Услуги в заказе")
        vb = QVBoxLayout(grp_services)

        self.tbl_services = QTableWidget(0, 3)
        self.tbl_services.setHorizontalHeaderLabels(["Услуга", "Цена", ""])
        hdr = self.tbl_services.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tbl_services.verticalHeader().setVisible(False)
        self.tbl_services.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        vb.addWidget(self.tbl_services)

        # Панель добавления услуги
        add_row = QHBoxLayout()
        self.cmb_service = QComboBox()
        self.cmb_service.setSizePolicy(
            self.cmb_service.sizePolicy().horizontalPolicy(),
            self.cmb_service.sizePolicy().verticalPolicy()
        )
        add_row.addWidget(QLabel("Добавить услугу:"))
        add_row.addWidget(self.cmb_service, 1)

        self.btn_add_service = QPushButton("Добавить")
        self.btn_add_service.clicked.connect(self._on_add_service)
        add_row.addWidget(self.btn_add_service)

        self.btn_remove_service = QPushButton("Удалить выбранную")
        self.btn_remove_service.clicked.connect(self._on_remove_service)
        add_row.addWidget(self.btn_remove_service)

        vb.addLayout(add_row)

        self.lbl_total = QLabel("Итого: 0.00 ₽")
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        vb.addWidget(self.lbl_total)

        root.addWidget(grp_services, 1)

        # --- Кнопки сохранения ---
        btns = QHBoxLayout()
        btns.addStretch()
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.setDefault(True)
        self.btn_save.clicked.connect(self._on_save)
        btns.addWidget(self.btn_save)

        self.btn_cancel = QPushButton("Отмена")
        self.btn_cancel.clicked.connect(self.reject)
        btns.addWidget(self.btn_cancel)
        root.addLayout(btns)

        # Выбранные услуги: список словарей {service_id, service_name, price}
        self._selected_services = []

    # --------------------- Загрузка справочников ---------------------
    def _load_references(self):
        # Клиенты
        clients = client_repo.get_all_clients()
        self.cmb_client.clear()
        for c in clients:
            self.cmb_client.addItem(f"{c['name']}  ({c['details']})", c['client_id'])

        # Услуги (только активные)
        self.services_cache = order_repo.get_active_services()
        self.cmb_service.clear()
        for s in self.services_cache:
            self.cmb_service.addItem(f"{s['service_name']} — {s['price']:.2f} ₽", s['service_id'])

    # --------------------- Загрузка заказа при редактировании ---------------------
    def _load_order(self):
        data = order_repo.get_order(self.order_id)
        if not data:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден.")
            return

        self.edt_vessel.setText(data['vessel_code'])

        # Клиент
        idx = self.cmb_client.findData(data['client_id'])
        if idx >= 0:
            self.cmb_client.setCurrentIndex(idx)

        # Статус
        s_idx = self.cmb_status.findText(data['status'])
        if s_idx >= 0:
            self.cmb_status.setCurrentIndex(s_idx)

        # Услуги
        self._selected_services = order_repo.get_order_services(self.order_id)
        self._render_services_table()

    # --------------------- Работа с таблицей услуг ---------------------
    def _render_services_table(self):
        self.tbl_services.setRowCount(0)
        total = 0.0
        for row_idx, s in enumerate(self._selected_services):
            self.tbl_services.insertRow(row_idx)
            self.tbl_services.setItem(row_idx, 0, QTableWidgetItem(s['service_name']))
            price_item = QTableWidgetItem(f"{float(s['price']):.2f}")
            price_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tbl_services.setItem(row_idx, 1, price_item)
            # Кнопка "Удалить" в строке
            btn_del = QPushButton("✕")
            btn_del.setFixedWidth(32)
            btn_del.setProperty("row_index", row_idx)
            btn_del.clicked.connect(self._on_row_delete_clicked)
            self.tbl_services.setCellWidget(row_idx, 2, btn_del)
            total += float(s['price'])
        self.lbl_total.setText(f"Итого: {total:.2f} ₽")

    def _on_add_service(self):
        if self.cmb_service.count() == 0:
            QMessageBox.information(self, "Внимание", "Нет доступных услуг.")
            return
        sid = self.cmb_service.currentData()
        sname = self.cmb_service.currentText()
        price = next((s['price'] for s in self.services_cache if s['service_id'] == sid), 0)
        self._selected_services.append({
            "service_id": sid,
            "service_name": sname.split(" — ")[0],
            "price": float(price)
        })
        self._render_services_table()

    def _on_remove_service(self):
        row = self.tbl_services.currentRow()
        if row < 0 or row >= len(self._selected_services):
            return
        self._selected_services.pop(row)
        self._render_services_table()

    def _on_row_delete_clicked(self):
        btn = self.sender()
        row = btn.property("row_index")
        if 0 <= row < len(self._selected_services):
            self._selected_services.pop(row)
            self._render_services_table()

    # --------------------- Валидация и сохранение ---------------------
    def _validate(self):
        vessel = self.edt_vessel.text().strip()
        if not vessel:
            QMessageBox.warning(self, "Ошибка", "Укажите код судна.")
            return False
        if self.cmb_client.count() == 0:
            QMessageBox.warning(self, "Ошибка", "Нет доступных клиентов.")
            return False
        if not self._selected_services:
            QMessageBox.warning(self, "Ошибка", "Добавьте хотя бы одну услугу.")
            return False
        return True

    def _on_save(self):
        if not self._validate():
            return

        payload = {
            "vessel_code": self.edt_vessel.text().strip(),
            "client_id": self.cmb_client.currentData(),
            "employee_id": Session.get_user_id(),
            "status": self.cmb_status.currentText(),
            "services": self._selected_services,
        }

        try:
            if self.is_edit:
                order_repo.update_order(self.order_id, payload)
            else:
                order_repo.create_order(payload)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка сохранения", str(e))