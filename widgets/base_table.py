"""Общие компоненты таблиц: заполнение, сортировка, кнопки действий в строке."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Sequence

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget

from widgets.styles import button_style


class SortableTableWidgetItem(QTableWidgetItem):
    """Ячейка с корректной сортировкой чисел и дат (по sort_value)."""

    def __init__(self, text: str, sort_value: Any = None) -> None:
        super().__init__(text)
        self._sort_value = sort_value if sort_value is not None else text

    def __lt__(self, other: QTableWidgetItem) -> bool:
        other_value = getattr(other, "_sort_value", other.text())
        try:
            return float(self._sort_value) < float(other_value)
        except (ValueError, TypeError):
            return str(self._sort_value) < str(other_value)


def make_item(
    value: Any,
    *,
    center: bool = False,
    align_right: bool = False,
    sort_value: Any = None,
    user_data: Any = None,
    default: str = "",
) -> QTableWidgetItem:
    """Создать ячейку таблицы.

    Если задан sort_value, ячейка сортируется по нему, а не по тексту.
    """
    text = default if value is None else str(value)
    item: QTableWidgetItem = (
        SortableTableWidgetItem(text, sort_value) if sort_value is not None
        else QTableWidgetItem(text)
    )
    if center:
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
    elif align_right:
        item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if user_data is not None:
        item.setData(Qt.ItemDataRole.UserRole, user_data)
    return item


def populate_table(
    table: QTableWidget,
    rows: Sequence[dict[str, Any]] | None,
    fill_row: Callable[[QTableWidget, int, dict[str, Any]], None],
    sorting: bool = True,
    editable: bool = False,
) -> None:
    """Заполнить QTableWidget строками.

    Отключает сортировку на время заполнения (иначе строки «прыгают»),
    очищает таблицу и вызывает ``fill_row(table, row_idx, row)`` для каждой записи.
    ``sorting=False`` оставляет сортировку выключенной (для таблиц с cell-виджетами).
    ``editable=True`` разрешает редактирование ячеек (по умолчанию — только чтение).
    """
    from PyQt6.QtWidgets import QAbstractItemView
    table.setSortingEnabled(False)
    table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers if not editable else QAbstractItemView.EditTrigger.DoubleClicked)
    table.setRowCount(0)
    if rows:
        table.setRowCount(len(rows))
        for idx, row in enumerate(rows):
            fill_row(table, idx, row)
    table.setSortingEnabled(sorting)


@dataclass(frozen=True)
class RowAction:
    """Описание кнопки действия в строке таблицы."""
    text: str
    callback: Callable[[Any], None]
    tooltip: str = ""
    bg: str = "#3498DB"
    hover: str = "#2980B9"


class ActionButtonsWidget(QWidget):
    """Набор кнопок действий для строки таблицы.

    Каждая кнопка вызывает ``callback(row_id)``. При ``enabled=False`` все кнопки
    отключаются, а в подсказке показывается ``disabled_tooltip``.
    """

    def __init__(
        self,
        row_id: Any,
        actions: Sequence[RowAction],
        enabled: bool = True,
        disabled_tooltip: str = "",
        button_size: tuple[int, int] = (65, 32),
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        for action in actions:
            btn = QPushButton(action.text)
            btn.setFixedSize(*button_size)
            btn.setEnabled(enabled)
            btn.setToolTip(action.tooltip if enabled else disabled_tooltip)
            btn.setStyleSheet(button_style(action.bg, action.hover, padding="0px", radius=4))
            btn.clicked.connect(lambda _checked=False, cb=action.callback: cb(row_id))
            layout.addWidget(btn)


__all__ = [
    "SortableTableWidgetItem", "make_item", "populate_table",
    "RowAction", "ActionButtonsWidget",
]
