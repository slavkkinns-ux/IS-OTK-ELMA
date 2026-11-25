"""Вспомогательные функции для диалогов: сообщения, обработка ошибок, фабрики виджетов."""

from __future__ import annotations

import logging
from collections.abc import Callable

from PyQt6.QtWidgets import (
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

logger = logging.getLogger("IS_OTK.ui")


def show_info(parent: QWidget, title: str, message: str) -> None:
    """Показать информационное сообщение."""
    QMessageBox.information(parent, title, message)


def show_warning(parent: QWidget, title: str, message: str) -> None:
    """Показать предупреждение."""
    QMessageBox.warning(parent, title, message)


def show_error(parent: QWidget, title: str, message: str) -> None:
    """Показать ошибку."""
    QMessageBox.critical(parent, title, message)


def handle_error(
    parent: QWidget,
    exc: BaseException,
    action: str = "Операция не выполнена",
) -> None:
    """Единая обработка ошибки в UI: сообщение пользователю + запись в лог.

    - ValueError: ошибка ввода. Предупреждение, в лог INFO.
    - PermissionError: нарушение правил доступа. Ошибка, в лог WARNING.
    - остальное: непредвиденный сбой. Ошибка с текстом ``action``, в лог ERROR с traceback.
    """
    if isinstance(exc, ValueError):
        logger.info("Ошибка ввода: %s", exc)
        show_warning(parent, "Ошибка валидации", str(exc))
    elif isinstance(exc, PermissionError):
        logger.warning("Отказ в доступе: %s", exc)
        show_error(parent, "Отказ в доступе", str(exc))
    else:
        logger.error("%s", action, exc_info=exc)
        show_error(parent, "Ошибка", f"{action}:\n{exc}")


def show_question(
    parent: QWidget,
    title: str,
    message: str,
    yes_text: str = "Да",
    no_text: str = "Нет",
    icon: QMessageBox.Icon = QMessageBox.Icon.Question,
) -> bool:
    """Показать вопрос с кнопками на русском. Возвращает True при выборе «Да».

    Кнопка «Нет» выбрана по умолчанию, чтобы случайное нажатие Enter
    не подтверждало опасное действие.
    """
    box = QMessageBox(parent)
    box.setIcon(icon)
    box.setWindowTitle(title)
    box.setText(message)
    btn_yes = box.addButton(yes_text, QMessageBox.ButtonRole.YesRole)
    btn_no = box.addButton(no_text, QMessageBox.ButtonRole.NoRole)
    box.setDefaultButton(btn_no)
    box.exec()
    return box.clickedButton() is btn_yes


def create_button(
    text: str,
    on_click: Callable[[], None] | None = None,
    style: str = "",
    fixed_width: int | None = None,
) -> QPushButton:
    """Создать кнопку с опциональным стилем и обработчиком."""
    btn = QPushButton(text)
    if on_click is not None:
        btn.clicked.connect(on_click)
    if style:
        btn.setStyleSheet(style)
    if fixed_width:
        btn.setFixedWidth(fixed_width)
    return btn


def create_label(text: str, bold: bool = False, style: str = "") -> QLabel:
    """Создать метку. Явный style имеет приоритет над bold."""
    lbl = QLabel(text)
    if style:
        lbl.setStyleSheet(style)
    elif bold:
        lbl.setStyleSheet("font-weight: bold;")
    return lbl


def create_form_group(title: str, parent: QWidget | None = None) -> tuple[QGroupBox, QFormLayout]:
    """Создать группу с QFormLayout. Возвращает (группа, layout формы)."""
    group = QGroupBox(title, parent)
    form = QFormLayout(group)
    return group, form


__all__ = [
    "show_info", "show_warning", "show_error", "show_question", "handle_error",
    "create_button", "create_label", "create_form_group",
]
