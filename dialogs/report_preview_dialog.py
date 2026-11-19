"""Диалог предварительного просмотра отчёта."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QTableWidget, QTableWidgetItem,
    QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt6.QtCore import Qt
from db import order_repo, report_repo
from datetime import datetime, date
import os
import sys


def format_date(value) -> str:
    if value is None:
        return ''
    if isinstance(value, datetime):
        return value.strftime('%d.%m.%Y')
    if isinstance(value, date):
        return value.strftime('%d.%m.%Y')
    return str(value)


class ReportPreviewDialog(QDialog):
    """Диалог предварительного просмотра отчёта."""

    def __init__(self, parent, order_id: int):
        super().__init__(parent)
        self.order_id = order_id
        self.report_id = None
        self.file_path = None
        self.setWindowTitle("Предварительный просмотр отчёта")
        self.setMinimumWidth(700)
        self.setMinimumHeight(600)
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        root = QVBoxLayout(self)

        # Заголовок
        title = QLabel("ОТЧЁТ ПО ЗАКАЗУ")
        title.setStyleSheet("""
            font-size: 18pt;
            font-weight: bold;
            color: #174A7E;
            padding: 10px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        # Информация о заказе
        info_box = QGroupBox("Информация о заказе")
        info_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #CBD7E4;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        info_lay = QFormLayout(info_box)
        info_lay.setSpacing(8)

        self.lblOrderId = QLabel()
        self.lblVesselCode = QLabel()
        self.lblClient = QLabel()
        self.lblEmployee = QLabel()
        self.lblDate = QLabel()
        self.lblStatus = QLabel()

        for label in [self.lblOrderId, self.lblVesselCode, self.lblClient,
                      self.lblEmployee, self.lblDate, self.lblStatus]:
            label.setStyleSheet("font-size: 10pt;")

        info_lay.addRow("Номер заказа:", self.lblOrderId)
        info_lay.addRow("Код сосуда:", self.lblVesselCode)
        info_lay.addRow("Клиент:", self.lblClient)
        info_lay.addRow("Сотрудник:", self.lblEmployee)
        info_lay.addRow("Дата:", self.lblDate)
        info_lay.addRow("Статус:", self.lblStatus)

        root.addWidget(info_box)

        # Таблица услуг
        services_box = QGroupBox("Выполненные исследования")
        services_box.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                font-size: 11pt;
                border: 1px solid #CBD7E4;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        services_lay = QVBoxLayout(services_box)

        self.tableServices = QTableWidget()
        self.tableServices.setColumnCount(3)
        self.tableServices.setHorizontalHeaderLabels(["№", "Услуга", "Стоимость"])
        self.tableServices.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tableServices.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.tableServices.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.tableServices.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.tableServices.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.tableServices.verticalHeader().setVisible(False)

        self.tableServices.setStyleSheet("""
            QHeaderView::section {
                background-color: #174A7E;
                color: white;
                font-weight: bold;
                padding: 5px;
                border: 1px solid #CBD7E4;
            }
            QTableWidget {
                border: 1px solid #CBD7E4;
                gridline-color: #CBD7E4;
            }
        """)

        services_lay.addWidget(self.tableServices)
        root.addWidget(services_box)

        # Итого
        total_lay = QHBoxLayout()
        total_lay.addWidget(QLabel("ИТОГО:"))
        self.lblTotal = QLabel("0.00 ₽")
        self.lblTotal.setStyleSheet("""
            font-size: 12pt;
            font-weight: bold;
            color: #174A7E;
            padding: 5px;
        """)
        total_lay.addWidget(self.lblTotal)
        total_lay.addStretch()
        root.addLayout(total_lay)

        # Подпись
        self.lblFooter = QLabel()
        self.lblFooter.setStyleSheet("font-size: 9pt; color: #666; padding: 10px;")
        self.lblFooter.setAlignment(Qt.AlignmentFlag.AlignRight)
        root.addWidget(self.lblFooter)

        # Кнопки
        btns = QHBoxLayout()
        btn_create = QPushButton("Создать PDF")
        btn_create.clicked.connect(self._create_pdf)
        btn_open = QPushButton("Открыть PDF")
        btn_open.clicked.connect(self._open_pdf)
        btn_print = QPushButton("Печать")
        btn_print.clicked.connect(self._print_pdf)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.reject)
        
        btns.addWidget(btn_create)
        btns.addWidget(btn_open)
        btns.addWidget(btn_print)
        btns.addStretch()
        btns.addWidget(btn_close)
        root.addLayout(btns)

    def _load_data(self):
        """Загрузить данные заказа и отобразить в диалоге."""
        order = order_repo.get_order(self.order_id)
        if not order:
            QMessageBox.warning(self, "Ошибка", "Заказ не найден.")
            return

        self.lblOrderId.setText(str(order['order_id']))
        self.lblVesselCode.setText(order['vessel_code'])
        self.lblClient.setText(order['client_name'] or '')
        self.lblEmployee.setText(order['employee_name'] or '')
        self.lblDate.setText(format_date(order.get('order_date')))
        self.lblStatus.setText(order['status'] or '')

        # Загрузка услуг
        services = order_repo.get_order_services(self.order_id)
        self.tableServices.setRowCount(len(services))
        total = 0.0

        for row_idx, s in enumerate(services):
            item_num = QTableWidgetItem(str(row_idx + 1))
            item_num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.tableServices.setItem(row_idx, 0, item_num)

            item_service = QTableWidgetItem(s['service_name'])
            self.tableServices.setItem(row_idx, 1, item_service)

            price = float(s['price'])
            total += price
            item_price = QTableWidgetItem(f"{price:.2f} ₽")
            item_price.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self.tableServices.setItem(row_idx, 2, item_price)

        self.lblTotal.setText(f"{total:.2f} ₽")
        self.lblFooter.setText(f"Отчёт сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}")

    def _create_pdf(self):
        """Создать PDF из текущего просмотра."""
        try:
            from report_generator import generate_report_pdf
            from session import Session

            employee_id = Session.get_user_id()
            self.file_path = generate_report_pdf(self.order_id)

            # Сохраняем в БД
            self.report_id = report_repo.create_report(self.order_id, employee_id, self.file_path)

            QMessageBox.information(
                self, "Отчёт создан",
                f"Отчёт ОТЧ-{self.report_id:04d} успешно создан.\nФайл: {self.file_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать отчёт:\n{e}")

    def _open_pdf(self):
        """Открыть созданный PDF."""
        if not self.file_path or not os.path.exists(self.file_path):
            QMessageBox.warning(self, "Ошибка", "PDF ещё не создан. Нажмите 'Создать PDF'.")
            return

        try:
            if sys.platform == 'win32':
                os.startfile(self.file_path)
            elif sys.platform == 'darwin':
                import subprocess
                subprocess.Popen(['open', self.file_path])
            else:
                import subprocess
                subprocess.Popen(['xdg-open', self.file_path])
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл:\n{e}")

    def _print_pdf(self):
        """Отправить PDF на печать."""
        if not self.file_path or not os.path.exists(self.file_path):
            QMessageBox.warning(self, "Ошибка", "PDF ещё не создан. Нажмите 'Создать PDF'.")
            return

        try:
            import subprocess
            if sys.platform == 'win32':
                os.startfile(self.file_path, 'print')
            else:
                subprocess.Popen(['lp', self.file_path])
            QMessageBox.information(self, "Печать", "Отчёт отправлен на печать.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось отправить на печать:\n{e}")