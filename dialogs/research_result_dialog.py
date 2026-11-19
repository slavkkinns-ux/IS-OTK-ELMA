"""Диалог просмотра результата исследования."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout
)
from PyQt6.QtCore import Qt
from db import report_repo
from datetime import datetime, date


def format_date(value) -> str:
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return str(value)


class ResearchResultDialog(QDialog):
    """Диалог просмотра результата исследования."""

    def __init__(self, parent, order_service_id: int, research_info: dict = None):
        super().__init__(parent)
        self.order_service_id = order_service_id
        self.research_info = research_info or {}
        self.setWindowTitle("Результат исследования")
        self.setMinimumWidth(500)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Блок информации об исследовании
        if self.research_info:
            info_box = QGroupBox("Информация об исследовании")
            info_lay = QFormLayout(info_box)
            info_lay.addRow("Заказ:", QLabel(str(self.research_info.get('order_id', ''))))
            info_lay.addRow("Код сосуда:", QLabel(str(self.research_info.get('vessel_code', ''))))
            info_lay.addRow("Клиент:", QLabel(self.research_info.get('client_name', '')))
            info_lay.addRow("Услуга:", QLabel(self.research_info.get('service_name', '')))
            root.addWidget(info_box)

        # Блок результата
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

        root.addWidget(result_box)

        # Кнопки
        btns = QHBoxLayout()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btn_close.setMinimumWidth(100)
        btns.addStretch()
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load_data(self):
        result = report_repo.get_research_result(self.order_service_id)
        if not result:
            self.lblResultValue.setText("Результат ещё не сохранён.")
            self.lblConclusion.setText('')
            self.lblResultDate.setText('')
            self.lblEmployee.setText('')
            return

        self.lblResultValue.setText(str(result.get('result_value', '') or 'Не указан'))
        self.lblConclusion.setText(str(result.get('conclusion', '') or 'Не указано'))
        self.lblResultDate.setText(format_date(result.get('result_date')))

        # Если есть employee_id — можно показать имя сотрудника
        employee_id = result.get('employee_id')
        if employee_id:
            employees = report_repo.get_all_employees()
            emp = next((e for e in employees if e['employee_id'] == employee_id), None)
            self.lblEmployee.setText(emp['full_name'] if emp else f"ID: {employee_id}")
        else:
            self.lblEmployee.setText('Не указан')