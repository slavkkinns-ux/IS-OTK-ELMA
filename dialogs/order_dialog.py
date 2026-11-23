"""Диалог создания/редактирования заказа."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFormLayout, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QScrollArea, QVBoxLayout, QWidget,
)

from db import client_repo as _default_client_repo
from db import order_repo as _default_order_repo
from db import services_repo as _default_services_repo
from services.client_service import ClientService
from services.order_service import OrderService
from services.service_service import ServiceService
from session import Session
from widgets.base_dialog import BaseDialog
from widgets.styles import HINT_STYLE, TOTAL_VALUE_STYLE, button_style

_SCROLL_STYLE = """
    QScrollArea {
        border: 1px solid #CBD7E4;
        border-radius: 4px;
        background-color: #FAFBFC;
    }
"""


class OrderDialog(BaseDialog):
    """Создание или редактирование заказа через сервисы."""

    def __init__(self, parent: QWidget | None, order_id: int | None = None,
                 order_service: OrderService | None = None,
                 client_service: ClientService | None = None,
                 service_service: ServiceService | None = None) -> None:
        super().__init__(
            parent,
            title="Новый заказ" if order_id is None else "Редактирование заказа",
            min_width=560, min_height=600,
        )
        self.order_id = order_id
        self.order_service = order_service or OrderService(
            _default_order_repo, _default_client_repo, _default_services_repo
        )
        self.client_service = client_service or ClientService(_default_client_repo)
        self.service_service = service_service or ServiceService(_default_services_repo)

        self.all_services: list[dict[str, Any]] = self.order_service.get_active_services()
        self.service_checks: list[QCheckBox] = []

        self._setup_ui()
        self._reload_clients()
        if self.order_id is not None:
            self._load_order()
        else:
            self._fill_suggested_code()

    # ==================== ПОСТРОЕНИЕ ====================

    def _setup_ui(self) -> None:
        self.root.addWidget(self._build_code_box())
        self.root.addWidget(self._build_client_box())
        self.root.addWidget(self._build_services_box())

        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("Итого:"))
        self.lblTotal = QLabel("0.00 ₽")
        self.lblTotal.setStyleSheet(TOTAL_VALUE_STYLE)
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        self.root.addLayout(total_lay)

        self.add_save_cancel_buttons(self._save)

    def _build_code_box(self) -> QGroupBox:
        box = QGroupBox("Код лабораторного сосуда")
        lay = QFormLayout(box)
        self.editVesselCode = QLineEdit()
        self.editVesselCode.setPlaceholderText("Например: С-0042")
        lay.addRow("Код сосуда:", self.editVesselCode)
        return box

    def _build_client_box(self) -> QGroupBox:
        box = QGroupBox("Заказчик")
        lay = QFormLayout(box)

        self.comboClientType = QComboBox()
        self.comboClientType.addItems(["ЮЛ", "ФЛ"])
        self.comboClientType.currentTextChanged.connect(self._reload_clients)
        lay.addRow("Тип заказчика:", self.comboClientType)

        self.comboClient = QComboBox()
        lay.addRow("Клиент:", self.comboClient)

        row = QHBoxLayout()
        self.btnNewClient = QPushButton("+ Добавить нового клиента")
        self.btnNewClient.clicked.connect(self._open_new_client_dialog)
        row.addWidget(self.btnNewClient)

        self.btnRefreshServices = QPushButton("🔄 Обновить услуги")
        self.btnRefreshServices.clicked.connect(self._reload_services)
        row.addWidget(self.btnRefreshServices)

        self.btnManageServices = QPushButton("⚙ Услуги")
        self.btnManageServices.setToolTip("Добавить, изменить или удалить услуги")
        self.btnManageServices.setStyleSheet(button_style("#2e86c1", "#2471a3", padding="8px 14px"))
        self.btnManageServices.clicked.connect(self._open_services_dialog)
        row.addWidget(self.btnManageServices)
        row.addStretch()
        lay.addRow(row)
        return box

    def _build_services_box(self) -> QGroupBox:
        box = QGroupBox("Исследования / услуги")
        lay = QVBoxLayout(box)

        search_lay = QHBoxLayout()
        search_lay.addWidget(QLabel("🔍 Поиск:"))
        self.editServiceSearch = QLineEdit()
        self.editServiceSearch.setPlaceholderText("Введите название услуги...")
        self.editServiceSearch.textChanged.connect(self._filter_services)
        search_lay.addWidget(self.editServiceSearch)
        lay.addLayout(search_lay)

        self.lblServiceCount = QLabel("0 из 0")
        self.lblServiceCount.setStyleSheet(HINT_STYLE)
        self.lblServiceCount.setAlignment(Qt.AlignmentFlag.AlignRight)
        lay.addWidget(self.lblServiceCount)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(200)
        scroll.setMaximumHeight(300)
        scroll.setStyleSheet(_SCROLL_STYLE)
        scroll_widget = QWidget()
        self.services_layout = QVBoxLayout(scroll_widget)
        self.services_layout.setContentsMargins(8, 8, 8, 8)
        self.services_layout.setSpacing(4)
        self._build_services_list()
        scroll.setWidget(scroll_widget)
        lay.addWidget(scroll)
        return box

    # ==================== УСЛУГИ ====================

    def _open_services_dialog(self) -> None:
        from dialogs.services_dialog import ServicesDialog
        ServicesDialog(self, service_service=self.service_service).exec()
        self._reload_services()

    def _build_services_list(self) -> None:
        while self.services_layout.count() > 0:
            item = self.services_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.service_checks.clear()

        if not self.all_services:
            empty = QLabel("Нет доступных услуг. Добавьте их через «⚙ Услуги».")
            empty.setStyleSheet("color: gray; font-style: italic; padding: 10px;")
            self.services_layout.addWidget(empty)
            self._update_service_count(0, 0)
            return

        for s in self.all_services:
            cb = QCheckBox(f"{s['service_name']}  —  {float(s['price']):.2f} ₽")
            cb.service_id = s["service_id"]  # type: ignore[attr-defined]
            cb.price = float(s["price"])  # type: ignore[attr-defined]
            cb.stateChanged.connect(self._recalc_total)
            cb.setMinimumHeight(28)
            self.service_checks.append(cb)
            self.services_layout.addWidget(cb)

        self.services_layout.addStretch()
        self._update_service_count(len(self.service_checks), len(self.all_services))

    def _filter_services(self) -> None:
        query = self.editServiceSearch.text().strip().lower()
        visible = 0
        for cb in self.service_checks:
            show = not query or query in cb.text().lower()
            cb.setVisible(show)
            visible += show
        self._update_service_count(visible, len(self.all_services))

    def _update_service_count(self, visible: int, total: int) -> None:
        if total == 0:
            self.lblServiceCount.setText("Нет услуг")
        elif visible == total:
            self.lblServiceCount.setText(f"Всего: {total}")
        else:
            self.lblServiceCount.setText(f"Найдено: {visible} из {total}")

    def _reload_services(self) -> None:
        self.all_services = self.order_service.get_active_services()
        self.editServiceSearch.clear()
        self._build_services_list()

    def _recalc_total(self) -> None:
        total = sum(cb.price for cb in self.service_checks if cb.isChecked())  # type: ignore[attr-defined]
        self.lblTotal.setText(f"{total:.2f} ₽")

    # ==================== КЛИЕНТЫ ====================

    def _fill_suggested_code(self) -> None:
        self.editVesselCode.setText(self.order_service.get_next_vessel_code())
        self.editVesselCode.selectAll()

    def _reload_clients(self) -> None:
        clients = self.client_service.get_clients_by_type(self.comboClientType.currentText())
        self.comboClient.clear()
        for c in clients:
            display = f"{c['name']} ({c['contact_person']})" if c.get("contact_person") else c["name"]
            self.comboClient.addItem(display, c["client_id"])

    def _open_new_client_dialog(self) -> None:
        from dialogs.client_dialog import ClientDialog
        dlg = ClientDialog(self, initial_type=self.comboClientType.currentText(),
                           client_service=self.client_service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._reload_clients()
            if self.comboClient.count() > 0:
                self.comboClient.setCurrentIndex(self.comboClient.count() - 1)

    # ==================== ЗАГРУЗКА ЗАКАЗА ====================

    def _load_order(self) -> None:
        order = self.order_service.get_order(self.order_id)
        if not order:
            return

        self.editVesselCode.setText(order["vessel_code"])

        # Смена типа вызывает _reload_clients через сигнал
        self.comboClientType.setCurrentText(order.get("client_type", "ЮЛ"))
        self._reload_clients()
        index = self.comboClient.findData(order["client_id"])
        if index >= 0:
            self.comboClient.setCurrentIndex(index)

        service_ids = {s["service_id"] for s in self.order_service.get_order_services(self.order_id)}
        for cb in self.service_checks:
            cb.blockSignals(True)
            cb.setChecked(cb.service_id in service_ids)  # type: ignore[attr-defined]
            cb.blockSignals(False)

        QTimer.singleShot(0, self._recalc_total)

    # ==================== СОХРАНЕНИЕ ====================

    def _selected_checks(self) -> list[QCheckBox]:
        return [cb for cb in self.service_checks if cb.isChecked() and cb.isVisible()]

    def _save(self) -> None:
        """Проверить форму и сохранить заказ. Бизнес-валидацию выполняет OrderService."""
        code = self.editVesselCode.text().strip()
        if not code:
            raise ValueError("Введите код сосуда.")
        if self.order_service.vessel_code_exists(
            code, exclude_archived=True, exclude_order_id=self.order_id
        ):
            raise ValueError(
                f"Код «{code}» уже используется в активных заказах.\n"
                "Введите другой или используйте предложенный."
            )
        if self.comboClient.count() == 0:
            raise ValueError("Выберите клиента или добавьте нового.")

        selected = self._selected_checks()
        if not selected:
            raise ValueError("Выберите хотя бы одну услугу.")

        payload = dict(
            vessel_code=code,
            client_id=self.comboClient.currentData(),
            employee_id=Session.get_user_id() or 0,
            service_ids=[cb.service_id for cb in selected],  # type: ignore[attr-defined]
            total_price=sum(cb.price for cb in selected),  # type: ignore[attr-defined]
        )

        if self.order_id is None:
            self.order_service.create_order(**payload)
            self.info("Готово", "Заказ успешно создан.")
        else:
            self.order_service.update_order(order_id=self.order_id, **payload)
            self.info("Готово", "Заказ успешно обновлён.")
        self.accept()


__all__ = ["OrderDialog"]
