"""Диалог просмотра результата исследования."""

from __future__ import annotations

from typing import Any

from PyQt6.QtWidgets import QFormLayout, QGroupBox, QLabel, QWidget

from db import employee_repo as _default_employee_repo
from db import report_repo as _default_report_repo
from services.employee_service import EmployeeService
from services.report_service import ReportService
from utils.formatting import format_date
from widgets.base_dialog import BaseDialog


class ResearchResultDialog(BaseDialog):
    """Просмотр сохранённого результата исследования."""

    def __init__(self, parent: QWidget | None, order_service_id: int,
                 research_info: dict[str, Any] | None = None,
                 report_service: ReportService | None = None,
                 employee_service: EmployeeService | None = None) -> None:
        super().__init__(parent, title="Результат исследования", min_width=500)
        # order_repo для этого диалога не нужен
        self.report_service = report_service or ReportService(_default_report_repo, None)
        self.employee_service = employee_service or EmployeeService(_default_employee_repo)
        self.order_service_id = order_service_id
        self.research_info = research_info or {}
        self._build_ui()
        self._load_data()

    def _build_ui(self) -> None:
        if self.research_info:
            info_box = QGroupBox("Информация об исследовании")
            info_lay = QFormLayout(info_box)
            info = self.research_info
            info_lay.addRow("Заказ:", QLabel(str(info.get("order_id", ""))))
            info_lay.addRow("Код сосуда:", QLabel(str(info.get("vessel_code", ""))))
            info_lay.addRow("Клиент:", QLabel(info.get("client_name", "")))
            info_lay.addRow("Услуга:", QLabel(info.get("service_name", "")))
            self.root.addWidget(info_box)

        result_box = QGroupBox("Результат исследования")
        result_lay = QFormLayout(result_box)

        self.lblResultValue = QLabel()
        self.lblResultValue.setWordWrap(True)
        self.lblResultValue.setStyleSheet("font-size: 11pt; color: #174A7E;")
        result_lay.addRow("Результат:", self.lblResultValue)

        self.lblConclusion = QLabel()
        self.lblConclusion.setWordWrap(True)
        result_lay.addRow("Заключение:", self.lblConclusion)

        self.lblResultDate = QLabel()
        result_lay.addRow("Дата:", self.lblResultDate)

        self.lblEmployee = QLabel()
        result_lay.addRow("Сотрудник:", self.lblEmployee)

        self.root.addWidget(result_box)
        self.add_close_button()

    def _load_data(self) -> None:
        result = self.report_service.get_research_result(self.order_service_id)
        if not result:
            self.lblResultValue.setText("Результат ещё не сохранён.")
            return

        self.lblResultValue.setText(str(result.get("result_value") or "Не указан"))
        self.lblConclusion.setText(str(result.get("conclusion") or "Не указано"))
        self.lblResultDate.setText(format_date(result.get("result_date")))

        employee_id = result.get("employee_id")
        if not employee_id:
            self.lblEmployee.setText("Не указан")
            return
        employee = self.employee_service.get_employee_by_id(int(employee_id))
        self.lblEmployee.setText(employee["full_name"] if employee else f"ID: {employee_id}")


__all__ = ["ResearchResultDialog"]
