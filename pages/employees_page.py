"""Страница управления сотрудниками."""

from __future__ import annotations

from typing import Any

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)

from db import employee_repo as _default_employee_repo
from dialogs.employee_dialog import ROLE_DISPLAY, EmployeeDialog
from services.employee_service import EmployeeService
from session import Session
from utils.formatting import format_date
from widgets.base_table import ActionButtonsWidget, RowAction, make_item, populate_table
from widgets.dialog_helpers import show_error, show_info, show_question, show_warning
from widgets.styles import (
    DEFAULT_ROLE_COLOR,
    PRIMARY_BUTTON_STYLE,
    ROLE_COLORS,
    STAT_CARD_STYLE,
    SUCCESS_BUTTON_STYLE,
    TABLE_CARD_STYLE,
)

# (ключ в статистике, заголовок карточки)
_STAT_CARDS: list[tuple[str, str]] = [
    ("total", "Всего"),
    ("active", "Активных"),
    ("managers", "Менеджеров"),
    ("lab_technicians", "Лаборантов"),
    ("controllers", "Контролёров"),
    ("admins", "Админов"),
]

_COLUMNS: list[str] = [
    "№", "ФИО", "Логин", "Роль", "Статус",
    "Исследований", "Отчётов", "Дата добавления", "Действия",
]
_COL_ACTIONS = len(_COLUMNS) - 1
_OTHER_ADMIN_HINT = "Только для своего аккаунта"


class EmployeesPage(QWidget):
    """Страница управления сотрудниками.

    Работает с данными через EmployeeService.
    """

    def __init__(self, parent: QWidget | None = None,
                 employee_service: EmployeeService | None = None) -> None:
        super().__init__(parent)
        self.service = employee_service or EmployeeService(_default_employee_repo)
        self.stat_cards: dict[str, QGroupBox] = {}
        self._init_ui()
        self._load_data()

    # ------------------------------------------------------------------
    # Построение интерфейса
    # ------------------------------------------------------------------

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        lbl_title = QLabel("Управление сотрудниками")
        lbl_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #174A7E;")
        main_layout.addWidget(lbl_title)

        lbl_subtitle = QLabel("Добавление и управление учётными записями персонала")
        lbl_subtitle.setStyleSheet("font-size: 10pt; color: #7F8C8D;")
        main_layout.addWidget(lbl_subtitle)

        main_layout.addLayout(self._build_stat_cards())
        main_layout.addWidget(self._build_filters())
        self._build_table()
        main_layout.addWidget(self.table_employees, stretch=1)
        main_layout.addLayout(self._build_bottom_buttons())

    def _build_stat_cards(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(10)
        for key, title in _STAT_CARDS:
            card = self._create_stat_card(title)
            layout.addWidget(card, stretch=1)
            self.stat_cards[key] = card
        return layout

    def _create_stat_card(self, title: str) -> QGroupBox:
        card = QGroupBox()
        card.setStyleSheet(STAT_CARD_STYLE)
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-size: 10pt; color: #174A7E; font-weight: bold;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)

        lbl_value = QLabel("0")
        lbl_value.setStyleSheet("font-size: 24pt; font-weight: bold; color: #2D83D5;")
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_value)

        card.lbl_value = lbl_value  # type: ignore[attr-defined]
        return card

    def _build_filters(self) -> QGroupBox:
        group = QGroupBox("Фильтры")
        layout = QHBoxLayout(group)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или логину...")
        self.search_edit.returnPressed.connect(self._load_data)
        layout.addWidget(self.search_edit, stretch=2)

        self.combo_role_filter = QComboBox()
        self.combo_role_filter.addItem("Все роли", None)
        for role_key, role_name in ROLE_DISPLAY.items():
            self.combo_role_filter.addItem(role_name, role_key)
        layout.addWidget(self.combo_role_filter)

        self.check_active_only = QCheckBox("Только активные")
        self.check_active_only.setChecked(True)
        layout.addWidget(self.check_active_only)

        btn_search = QPushButton("Поиск")
        btn_search.setStyleSheet(PRIMARY_BUTTON_STYLE)
        btn_search.clicked.connect(self._load_data)
        layout.addWidget(btn_search)

        btn_reset = QPushButton("Сбросить")
        btn_reset.clicked.connect(self._reset_filters)
        layout.addWidget(btn_reset)
        return group

    def _build_table(self) -> None:
        table = QTableWidget()
        table.setColumnCount(len(_COLUMNS))
        table.setHorizontalHeaderLabels(_COLUMNS)
        table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.verticalHeader().setDefaultSectionSize(50)
        table.verticalHeader().setMinimumSectionSize(50)

        header = table.horizontalHeader()
        header.setMinimumSectionSize(80)
        for col in range(len(_COLUMNS)):
            header.setSectionResizeMode(col, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(_COL_ACTIONS, QHeaderView.ResizeMode.Fixed)
        for col, width in ((0, 50), (5, 90), (6, 70), (7, 110), (_COL_ACTIONS, 220)):
            table.setColumnWidth(col, width)

        table.setStyleSheet(TABLE_CARD_STYLE)
        self.table_employees = table

    def _build_bottom_buttons(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.addStretch()

        self.btn_add = QPushButton("+ Добавить сотрудника")
        self.btn_add.setStyleSheet(SUCCESS_BUTTON_STYLE)
        self.btn_add.clicked.connect(self._on_add_employee)
        layout.addWidget(self.btn_add)

        self.btn_refresh = QPushButton("↻ Обновить")
        self.btn_refresh.clicked.connect(self._load_data)
        layout.addWidget(self.btn_refresh)
        return layout

    # ------------------------------------------------------------------
    # Данные
    # ------------------------------------------------------------------

    def _load_data(self) -> None:
        employees = self.service.get_employees(
            role_filter=self.combo_role_filter.currentData(),
            active_only=self.check_active_only.isChecked(),
            search_query=self.search_edit.text().strip() or None,
        )
        self._current_user_id = Session.get_user_id()
        # Сортировка выключена: в последней колонке стоят cell-виджеты
        populate_table(self.table_employees, employees, self._fill_row, sorting=False)
        self._update_stats()

    def _fill_row(self, table: QTableWidget, row_idx: int, emp: dict[str, Any]) -> None:
        employee_id: int = emp["employee_id"]
        role = emp.get("role", "")
        is_active = bool(emp.get("is_active", 1))
        is_other_admin = role == "admin" and employee_id != self._current_user_id

        table.setItem(row_idx, 0, make_item(row_idx + 1, center=True))
        table.setItem(row_idx, 1, make_item(emp.get("full_name")))
        table.setItem(row_idx, 2, make_item(emp.get("login")))

        item_role = make_item(ROLE_DISPLAY.get(role, role), center=True)
        item_role.setForeground(QColor("white"))
        item_role.setBackground(QColor(ROLE_COLORS.get(role, DEFAULT_ROLE_COLOR)))
        table.setItem(row_idx, 3, item_role)

        table.setItem(row_idx, 4, make_item("Активен" if is_active else "Деактивирован", center=True))
        table.setItem(row_idx, 5, make_item(emp.get("research_count", 0), center=True))
        table.setItem(row_idx, 6, make_item(emp.get("report_count", 0), center=True))
        table.setItem(row_idx, 7, make_item(format_date(emp.get("created_at")) or "-"))

        actions = [
            RowAction("Изм", self._on_edit_employee, "Редактировать", "#3498DB", "#2980B9"),
            RowAction("Пар", self._on_reset_password, "Сбросить пароль", "#F39C12", "#E67E22"),
            RowAction(
                "Блок" if is_active else "Разб", self._on_toggle_employee_status,
                "Деактивировать" if is_active else "Активировать", "#E74C3C", "#C0392B",
            ),
        ]
        table.setCellWidget(
            row_idx, _COL_ACTIONS,
            ActionButtonsWidget(employee_id, actions, enabled=not is_other_admin,
                                disabled_tooltip=_OTHER_ADMIN_HINT),
        )

    def _update_stats(self) -> None:
        stats = self.service.get_employee_stats()
        if not stats:
            return
        for key, card in self.stat_cards.items():
            card.lbl_value.setText(str(stats.get(key, 0)))  # type: ignore[attr-defined]

    def _reset_filters(self) -> None:
        self.search_edit.clear()
        self.combo_role_filter.setCurrentIndex(0)
        self.check_active_only.setChecked(True)
        self._load_data()

    # ------------------------------------------------------------------
    # Действия
    # ------------------------------------------------------------------

    def _run_action(self, action: Any, error_text: str) -> bool:
        """Выполнить действие сервиса и показать понятное сообщение при ошибке."""
        try:
            action()
            return True
        except ValueError as exc:
            show_warning(self, "Ошибка валидации", str(exc))
        except PermissionError as exc:
            show_error(self, "Отказ в доступе", str(exc))
        except Exception as exc:  # noqa: BLE001
            show_error(self, "Ошибка", f"{error_text}:\n{exc}")
        return False

    def _on_add_employee(self) -> None:
        dialog = EmployeeDialog(self, employee_service=self.service)
        if dialog.exec() == EmployeeDialog.DialogCode.Accepted:
            self._load_data()
            show_info(self, "Готово", "Сотрудник успешно добавлен.")

    def _on_edit_employee(self, employee_id: int) -> None:
        dialog = EmployeeDialog(self, employee_id=employee_id, employee_service=self.service)
        if dialog.exec() == EmployeeDialog.DialogCode.Accepted:
            self._load_data()
            show_info(self, "Готово", "Данные сотрудника обновлены.")

    def _on_reset_password(self, employee_id: int) -> None:
        if not show_question(
            self, "Сброс пароля",
            "Сбросить пароль сотрудника на '123456'?\n\n"
            "Сотрудник будет обязан сменить пароль при следующем входе.",
        ):
            return
        ok = self._run_action(
            lambda: self.service.reset_password(employee_id, Session.get_user_id()),
            "Не удалось сбросить пароль",
        )
        if ok:
            show_info(self, "Готово", "Пароль сброшен на '123456'.")

    def _on_toggle_employee_status(self, employee_id: int) -> None:
        result: dict[str, bool] = {}

        def action() -> None:
            result["status"] = self.service.toggle_employee_status(
                employee_id, Session.get_user_id()
            )

        if self._run_action(action, "Не удалось изменить статус"):
            self._load_data()
            text = "активирован" if result["status"] else "деактивирован"
            show_info(self, "Готово", f"Сотрудник {text}.")


__all__ = ["EmployeesPage"]
