"""Диалог просмотра заказа."""

from __future__ import annotations

from PyQt6.QtWidgets import (
    QAbstractItemView,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from db import order_repo as _default_order_repo
from services.order_service import OrderService
from utils.formatting import format_date
from widgets.base_dialog import BaseDialog
from widgets.base_table import make_item
from widgets.styles import TOTAL_VALUE_STYLE


class ViewOrderDialog(BaseDialog):
    """Просмотр заказа: шапка, список услуг, итоговая сумма."""

    def __init__(self, parent: QWidget | None, order_id: int,
                 order_service: OrderService | None = None) -> None:
        super().__init__(parent, title="Просмотр заказа", min_width=550)
        self.order_id = order_id
        # client_repo и service_repo для просмотра не нужны
        self.order_service = order_service or OrderService(_default_order_repo, None, None)
        self._setup_ui()
        self._load_order()

    def _setup_ui(self) -> None:
        info_box = QGroupBox("Информация о заказе")
        info_lay = QFormLayout(info_box)
        self.lblVesselCode = QLabel()
        self.lblClient = QLabel()
        self.lblEmployee = QLabel()
        self.lblDate = QLabel()
        self.lblStatus = QLabel()
        for caption, label in (
            ("Код сосуда:", self.lblVesselCode),
            ("Клиент:", self.lblClient),
            ("Сотрудник:", self.lblEmployee),
            ("Дата:", self.lblDate),
            ("Статус:", self.lblStatus),
        ):
            info_lay.addRow(caption, label)
        self.root.addWidget(info_box)

        services_box = QGroupBox("Услуги")
        services_lay = QVBoxLayout(services_box)
        self.tableServices = QTableWidget()
        self.tableServices.setColumnCount(2)
        self.tableServices.setHorizontalHeaderLabels(["Услуга", "Стоимость"])
        self.tableServices.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableServices.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableServices.verticalHeader().setVisible(False)
        header = self.tableServices.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.tableServices.setWordWrap(True)
        self.tableServices.verticalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.ResizeToContents
        )
        services_lay.addWidget(self.tableServices)
        self.root.addWidget(services_box)

        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("Итого:"))
        self.lblTotal = QLabel("0.00 RUB")
        self.lblTotal.setStyleSheet(TOTAL_VALUE_STYLE)
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        self.root.addLayout(total_lay)

        self.add_close_button()

    def _load_order(self) -> None:
        order = self.order_service.get_order(self.order_id)
        if not order:
            return

        self.lblVesselCode.setText(str(order.get("vessel_code", "")))
        self.lblClient.setText(str(order.get("client_name", "")))
        self.lblEmployee.setText(str(order.get("employee_name", "")))
        self.lblDate.setText(format_date(order.get("order_date")))
        self.lblStatus.setText(str(order.get("status", "")))

        services = self.order_service.get_order_services(self.order_id)
        self.tableServices.setRowCount(len(services))
        total = 0.0
        for row_idx, s in enumerate(services):
            price = float(s.get("price", 0))
            total += price
            self.tableServices.setItem(row_idx, 0, make_item(s.get("service_name")))
            self.tableServices.setItem(row_idx, 1, make_item(f"{price:.2f} RUB", align_right=True))
        self.lblTotal.setText(f"{total:.2f} RUB")


__all__ = ["ViewOrderDialog"]
