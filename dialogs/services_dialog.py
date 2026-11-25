"""Диалог управления услугами."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QWidget,
)

from db import services_repo as _default_services_repo
from services.service_service import ServiceService
from widgets.base_dialog import BaseDialog
from widgets.base_table import make_item, populate_table
from widgets.dialog_helpers import show_info, show_question, show_warning
from widgets.styles import TABLE_STYLE, TITLE_STYLE

_COLUMNS = ["ID", "Название услуги", "Цена, RUB", "Статус"]


class ServicesDialog(BaseDialog):
    """Диалог управления списком услуг (CRUD) через ServiceService."""

    def __init__(self, parent: QWidget | None,
                 service_service: ServiceService | None = None) -> None:
        super().__init__(parent, title="Управление услугами", min_width=700, min_height=500)
        self.service_service = service_service or ServiceService(_default_services_repo)
        self._build_ui()
        self._load_services()

    def _build_ui(self) -> None:
        title = QLabel("Список услуг")
        title.setStyleSheet(TITLE_STYLE)
        self.root.addWidget(title)

        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLUMNS))
        self.table.setHorizontalHeaderLabels(_COLUMNS)
        self.table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        for col in range(len(_COLUMNS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.setStyleSheet(TABLE_STYLE)
        self.root.addWidget(self.table)

        btns = QHBoxLayout()
        for text, handler in (
            ("+ Добавить", self._add_service),
            ("✎ Редактировать", self._edit_service),
            ("Включить/Отключить", self._toggle_service),
            ("✕ Удалить", self._delete_service),
        ):
            btn = QPushButton(text)
            btn.clicked.connect(handler)
            btns.addWidget(btn)
        btns.addStretch()
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.accept)
        btns.addWidget(btn_close)
        self.root.addLayout(btns)

    # ---------- данные ----------

    def _load_services(self) -> None:
        """Загрузить все услуги (включая отключённые) в таблицу."""
        services = self.service_service.get_all_services(include_inactive=True)
        populate_table(self.table, services, self._fill_row)

    @staticmethod
    def _fill_row(table: QTableWidget, row_idx: int, s: dict[str, Any]) -> None:
        is_active = bool(s["is_active"])
        gray = None if is_active else Qt.GlobalColor.gray

        item_name = make_item(s["service_name"])
        item_status = make_item("Активна" if is_active else "Отключена", center=True)
        if gray is not None:
            item_name.setForeground(gray)
            item_status.setForeground(gray)

        table.setItem(row_idx, 0, make_item(s["service_id"], center=True))
        table.setItem(row_idx, 1, item_name)
        table.setItem(row_idx, 2, make_item(f"{float(s['price']):.2f}", align_right=True))
        table.setItem(row_idx, 3, item_status)

    def _get_selected_service(self) -> dict[str, Any] | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        return {
            "service_id": int(self.table.item(row, 0).text()),
            "service_name": self.table.item(row, 1).text(),
            "price": float(self.table.item(row, 2).text()),
            "is_active": self.table.item(row, 3).text() == "Активна",
        }

    # ---------- действия ----------

    def _add_service(self) -> None:
        dlg = ServiceEditDialog(self, service=None, service_service=self.service_service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_services()

    def _edit_service(self) -> None:
        service = self._get_selected_service()
        if not service:
            show_info(self, "Редактирование", "Выберите услугу в таблице.")
            return
        dlg = ServiceEditDialog(self, service=service, service_service=self.service_service)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self._load_services()

    def _toggle_service(self) -> None:
        service = self._get_selected_service()
        if not service:
            show_info(self, "Статус", "Выберите услугу в таблице.")
            return
        action = "отключить" if service["is_active"] else "включить"
        if not show_question(
            self, "Подтверждение",
            f"Вы уверены, что хотите {action} услугу «{service['service_name']}»?",
        ):
            return
        try:
            self.service_service.toggle_service(service["service_id"])
            self._load_services()
        except ValueError as exc:
            show_warning(self, "Ошибка валидации", str(exc))
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось изменить статус:\n{exc}")

    def _delete_service(self) -> None:
        service = self._get_selected_service()
        if not service:
            show_info(self, "Удаление", "Выберите услугу в таблице.")
            return

        if self.service_service.is_service_used(service["service_id"]):
            if not show_question(
                self, "Удаление услуги",
                f"Услуга «{service['service_name']}» используется в существующих заказах.\n"
                "Удаление может нарушить целостность данных.\n\nПродолжить?",
                yes_text="Да, удалить", no_text="Отмена",
                icon=QMessageBox.Icon.Warning,
            ):
                return

        if not show_question(
            self, "Удаление услуги",
            f"Услуга «{service['service_name']}» будет удалена безвозвратно.\n\nПродолжить?",
            icon=QMessageBox.Icon.Warning,
        ):
            return

        try:
            self.service_service.delete_service(service["service_id"], soft=False)
            self._load_services()
            show_info(self, "Готово", "Услуга удалена.")
        except ValueError as exc:
            show_warning(self, "Ошибка валидации", str(exc))
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось удалить услугу:\n{exc}")


class ServiceEditDialog(BaseDialog):
    """Диалог добавления/редактирования услуги."""

    def __init__(self, parent: QWidget | None, service: dict[str, Any] | None,
                 service_service: ServiceService | None = None) -> None:
        super().__init__(
            parent,
            title="Новая услуга" if service is None else "Редактирование услуги",
            min_width=400,
        )
        self.service = service
        self.service_service = service_service or ServiceService(_default_services_repo)
        self._build_ui()
        if service:
            self.editName.setText(service["service_name"])
            self.editPrice.setText(f"{float(service['price']):.2f}")

    def _build_ui(self) -> None:
        name_lay = QHBoxLayout()
        name_lay.addWidget(QLabel("Название услуги:"))
        self.editName = QLineEdit()
        self.editName.setPlaceholderText("Например: Химический анализ")
        name_lay.addWidget(self.editName)
        self.root.addLayout(name_lay)

        price_lay = QHBoxLayout()
        price_lay.addWidget(QLabel("Цена (RUB):"))
        self.editPrice = QLineEdit()
        self.editPrice.setPlaceholderText("0.00")
        price_lay.addWidget(self.editPrice)
        self.root.addLayout(price_lay)

        self.add_save_cancel_buttons(self._save)

    def _parse_price(self) -> float:
        text = self.editPrice.text().strip().replace(",", ".")
        if not text:
            raise ValueError("Введите цену.")
        try:
            return float(text)
        except ValueError:
            raise ValueError("Некорректный формат цены.") from None

    def _save(self) -> None:
        """Сохранить услугу. Остальную валидацию (имя, дубликат, цена < 0) делает сервис."""
        name = self.editName.text().strip()
        price = self._parse_price()

        if self.service is None:
            self.service_service.add_service(name, price)
            self.info("Готово", "Услуга добавлена.")
        else:
            self.service_service.update_service(
                self.service["service_id"], name, price,
                1 if self.service["is_active"] else 0,
            )
            self.info("Готово", "Услуга обновлена.")
        self.accept()


__all__ = ["ServicesDialog", "ServiceEditDialog"]
