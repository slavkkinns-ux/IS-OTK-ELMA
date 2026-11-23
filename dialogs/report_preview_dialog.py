"""Диалог предварительного просмотра отчёта."""

from __future__ import annotations

import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView, QFormLayout, QGroupBox, QHBoxLayout, QHeaderView,
    QLabel, QPushButton, QTableWidget, QVBoxLayout, QWidget,
)

from db import order_repo as _default_order_repo
from db import report_repo as _default_report_repo
from services.order_service import OrderService
from services.report_service import ReportService
from session import Session
from utils.formatting import format_date
from widgets.base_dialog import BaseDialog
from widgets.base_table import make_item
from widgets.styles import GROUPBOX_TITLED_STYLE, HINT_STYLE, TABLE_STYLE


class ReportPreviewDialog(BaseDialog):
    """Предварительный просмотр отчёта по заказу с созданием, открытием и печатью PDF."""

    def __init__(self, parent: QWidget | None, order_id: int,
                 order_service: OrderService | None = None,
                 report_service: ReportService | None = None) -> None:
        super().__init__(parent, title="Предварительный просмотр отчёта",
                         min_width=700, min_height=600)
        self.order_service = order_service or OrderService(_default_order_repo, None, None)
        self.report_service = report_service or ReportService(
            _default_report_repo, _default_order_repo
        )
        self.order_id = order_id
        self.report_id: int | None = None
        self.file_path: str | None = None
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        title = QLabel("ОТЧЁТ ПО ЗАКАЗУ")
        title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #174A7E; padding: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.root.addWidget(title)

        info_box = QGroupBox("Информация о заказе")
        info_box.setStyleSheet(GROUPBOX_TITLED_STYLE)
        info_lay = QFormLayout(info_box)
        info_lay.setSpacing(8)
        self.lblOrderId = QLabel()
        self.lblVesselCode = QLabel()
        self.lblClient = QLabel()
        self.lblEmployee = QLabel()
        self.lblDate = QLabel()
        self.lblStatus = QLabel()
        for caption, label in (
            ("Номер заказа:", self.lblOrderId),
            ("Код сосуда:", self.lblVesselCode),
            ("Клиент:", self.lblClient),
            ("Сотрудник:", self.lblEmployee),
            ("Дата:", self.lblDate),
            ("Статус:", self.lblStatus),
        ):
            label.setStyleSheet("font-size: 10pt;")
            info_lay.addRow(caption, label)
        self.root.addWidget(info_box)

        services_box = QGroupBox("Выполненные исследования")
        services_box.setStyleSheet(GROUPBOX_TITLED_STYLE)
        services_lay = QVBoxLayout(services_box)
        self.tableServices = QTableWidget()
        self.tableServices.setColumnCount(3)
        self.tableServices.setHorizontalHeaderLabels(["№", "Услуга", "Стоимость"])
        self.tableServices.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableServices.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableServices.verticalHeader().setVisible(False)
        header = self.tableServices.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tableServices.setStyleSheet(TABLE_STYLE)
        services_lay.addWidget(self.tableServices)
        self.root.addWidget(services_box)

        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("ИТОГО:"))
        self.lblTotal = QLabel("0.00 ₽")
        self.lblTotal.setStyleSheet(
            "font-size: 12pt; font-weight: bold; color: #174A7E; padding: 5px;"
        )
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        self.root.addLayout(total_lay)

        self.lblFooter = QLabel()
        self.lblFooter.setStyleSheet(HINT_STYLE + " padding: 10px;")
        self.lblFooter.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.root.addWidget(self.lblFooter)

        btns = QHBoxLayout()
        for text, handler in (
            ("Создать PDF", self._create_pdf),
            ("Открыть PDF", self._open_pdf),
            ("Печать", self._print_pdf),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btns.addWidget(btn)
        btns.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.reject)
        btns.addWidget(btn_close)
        self.root.addLayout(btns)

    def _load_data(self) -> None:
        order = self.order_service.get_order(self.order_id)
        if not order:
            self.warn("Ошибка", "Заказ не найден.")
            return

        self.lblOrderId.setText(str(order["order_id"]))
        self.lblVesselCode.setText(order["vessel_code"])
        self.lblClient.setText(order["client_name"] or "")
        self.lblEmployee.setText(order["employee_name"] or "")
        self.lblDate.setText(format_date(order.get("order_date")))
        self.lblStatus.setText(order["status"] or "")

        services = self.order_service.get_order_services(self.order_id)
        self.tableServices.setRowCount(len(services))
        total = 0.0
        for row_idx, s in enumerate(services):
            price = float(s["price"])
            total += price
            self.tableServices.setItem(row_idx, 0, make_item(row_idx + 1, center=True))
            self.tableServices.setItem(row_idx, 1, make_item(s["service_name"]))
            self.tableServices.setItem(row_idx, 2, make_item(f"{price:.2f} ₽", align_right=True))

        self.lblTotal.setText(f"{total:.2f} ₽")
        self.lblFooter.setText(f"Отчёт сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    def _create_pdf(self) -> None:
        """Создать запись отчёта, сгенерировать PDF и сохранить путь к нему.

        Порядок такой же, как в главном окне: имя файла строится по report_id.
        """
        try:
            from report_generator import generate_report_pdf

            report_id = self.report_service.create_report(
                self.order_id, Session.get_user_id(), None
            )
            file_path = generate_report_pdf(
                self.order_id, report_id,
                order_service=self.order_service,
                report_service=self.report_service,
            )
            self.report_service.update_report_path(report_id, file_path)
            self.report_id, self.file_path = report_id, file_path

            self.info(
                "Отчёт создан",
                f"Отчёт ОТЧ-{report_id:04d} успешно создан.\nФайл: {file_path}",
            )
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось создать отчёт:\n{exc}")

    def _has_pdf(self) -> bool:
        if self.file_path and os.path.exists(self.file_path):
            return True
        self.warn("Ошибка", "PDF ещё не создан. Нажмите 'Создать PDF'.")
        return False

    def _open_pdf(self) -> None:
        if not self._has_pdf():
            return
        try:
            self.report_service.open_file(self.file_path)
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось открыть файл:\n{exc}")

    def _print_pdf(self) -> None:
        if not self._has_pdf():
            return
        try:
            self.report_service.print_file(self.file_path)
            self.info("Печать", "Отчёт отправлен на печать.")
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось отправить на печать:\n{exc}")


__all__ = ["ReportPreviewDialog"]
