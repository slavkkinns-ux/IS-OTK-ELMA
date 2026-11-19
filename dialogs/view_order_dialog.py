"""Диалог просмотра заказа."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QTableWidgetItem, QTableWidget,
    QAbstractItemView
)
from PyQt6 import QtCore
from db import order_repo


class ViewOrderDialog(QDialog):
    def __init__(self, parent, order_id: int):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle("Просмотр заказа")
        self.setMinimumWidth(500)
        self._setup_ui()
        self._load_order()

    def _setup_ui(self):
        root = QVBoxLayout(self)

        info_box = QGroupBox("Информация о заказе")
        info_lay = QFormLayout(info_box)

        self.lblVesselCode = QLabel()
        info_lay.addRow("Код сосуда:", self.lblVesselCode)

        self.lblClient = QLabel()
        info_lay.addRow("Клиент:", self.lblClient)

        self.lblEmployee = QLabel()
        info_lay.addRow("Сотрудник:", self.lblEmployee)

        self.lblDate = QLabel()
        info_lay.addRow("Дата:", self.lblDate)

        self.lblStatus = QLabel()
        info_lay.addRow("Статус:", self.lblStatus)

        root.addWidget(info_box)

        services_box = QGroupBox("Услуги")
        services_lay = QVBoxLayout(services_box)
        self.tableServices = QTableWidget()
        self.tableServices.setColumnCount(2)
        self.tableServices.setHorizontalHeaderLabels(["Услуга", "Стоимость"])
        self.tableServices.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableServices.horizontalHeader().setStretchLastSection(True)
        services_lay.addWidget(self.tableServices)
        root.addWidget(services_box)

        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("Итого:"))
        self.lblTotal = QLabel("0.00 ₽")
        self.lblTotal.setStyleSheet("font-size: 14pt; font-weight: bold; color: #174A7E;")
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        root.addLayout(total_lay)

        btns = QHBoxLayout()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btns.addStretch()
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load_order(self):
        order = order_repo.get_order(self.order_id)
        if not order:
            return

        self.lblVesselCode.setText(str(order.get('vessel_code', '')))
        self.lblClient.setText(str(order.get('client_name', '')))
        self.lblEmployee.setText(str(order.get('employee_name', '')))

        order_date = order.get('order_date')
        if order_date:
            self.lblDate.setText(str(order_date).split(' ')[0])
        else:
            self.lblDate.setText('')

        self.lblStatus.setText(str(order.get('status', '')))

        services = order_repo.get_order_services(self.order_id)
        self.tableServices.setRowCount(len(services))
        total = 0.0

        for row_idx, s in enumerate(services):
            self.tableServices.setItem(row_idx, 0, QTableWidgetItem(str(s.get('service_name', ''))))
            price = float(s.get('price', 0))
            total += price
            price_item = QTableWidgetItem(f"{price:.2f} ₽")
            price_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignRight | QtCore.Qt.AlignmentFlag.AlignVCenter)
            self.tableServices.setItem(row_idx, 1, price_item)

        self.lblTotal.setText(f"{total:.2f} ₽")