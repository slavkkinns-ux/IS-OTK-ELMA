from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QGroupBox,
    QLabel, QHeaderView, QTextEdit
)
from PyQt6.QtCore import Qt
from db import order_repo, report_repo


class ViewOrderDialog(QDialog):
    """Просмотр заказа в режиме read-only."""

    def __init__(self, parent, order_id: int):
        super().__init__(parent)
        self.order_id = order_id
        self.setWindowTitle(f"Заказ №{order_id}")
        self.setMinimumSize(760, 600)
        self._build_ui()
        self._load()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # --- Шапка заказа ---
        grp = QGroupBox("Информация о заказе")
        form = QFormLayout(grp)
        self.lbl_vessel = QLabel()
        self.lbl_client = QLabel()
        self.lbl_employee = QLabel()
        self.lbl_date = QLabel()
        self.lbl_status = QLabel()
        form.addRow("Код судна:", self.lbl_vessel)
        form.addRow("Клиент:", self.lbl_client)
        form.addRow("Сотрудник:", self.lbl_employee)
        form.addRow("Дата заказа:", self.lbl_date)
        form.addRow("Статус:", self.lbl_status)
        root.addWidget(grp)

        # --- Услуги ---
        grp2 = QGroupBox("Услуги и результаты исследований")
        vb = QVBoxLayout(grp2)
        self.tbl = QTableWidget(0, 4)
        self.tbl.setHorizontalHeaderLabels(["Услуга", "Цена", "Результат", "Заключение"])
        hdr = self.tbl.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.tbl.verticalHeader().setVisible(False)
        self.tbl.setWordWrap(True)
        vb.addWidget(self.tbl)
        root.addWidget(grp2, 1)

        # --- Итого ---
        self.lbl_total = QLabel()
        self.lbl_total.setStyleSheet("font-weight: bold; font-size: 14px;")
        root.addWidget(self.lbl_total)

        # --- Кнопка закрытия ---
        btns = QHBoxLayout()
        btns.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load(self):
        data = order_repo.get_order(self.order_id)
        if not data:
            return
        self.lbl_vessel.setText(data.get('vessel_code', ''))
        self.lbl_client.setText(data.get('client_name', ''))
        self.lbl_employee.setText(data.get('employee_name', ''))
        self.lbl_date.setText(str(data.get('order_date', '')))
        self.lbl_status.setText(data.get('status', ''))

        rows = report_repo.get_report_research(self.order_id)
        self.tbl.setRowCount(0)
        total = 0.0
        for r in rows:
            i = self.tbl.rowCount()
            self.tbl.insertRow(i)
            self.tbl.setItem(i, 0, QTableWidgetItem(r.get('service_name', '')))
            price = float(r.get('price_at_order') or 0)
            self.tbl.setItem(i, 1, QTableWidgetItem(f"{price:.2f}"))
            self.tbl.setItem(i, 2, QTableWidgetItem(r.get('result_value') or '—'))
            self.tbl.setItem(i, 3, QTableWidgetItem(r.get('conclusion') or '—'))
            total += price
        self.tbl.resizeRowsToContents()
        self.lbl_total.setText(f"Итого по заказу: {total:.2f} ₽")