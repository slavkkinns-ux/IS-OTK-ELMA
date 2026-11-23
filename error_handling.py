"""Глобальная обработка необработанных исключений.

В PyQt6 исключение в слоте без sys.excepthook завершает процесс (qFatal).
Здесь исключение пишется в лог, пользователю показывается сообщение,
приложение продолжает работать.
"""
from __future__ import annotations

import logging
import sys
from types import TracebackType

from PyQt6.QtWidgets import QApplication, QMessageBox

from logger import LOG_DIR

_logger = logging.getLogger("IS_OTK.errors")
_showing = False  # защита от лавины окон, если ошибка повторяется в цикле событий


def _handle_exception(
    exc_type: type[BaseException],
    exc: BaseException,
    tb: TracebackType | None,
) -> None:
    global _showing
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc, tb)
        return

    _logger.critical("Необработанное исключение", exc_info=(exc_type, exc, tb))

    if _showing or QApplication.instance() is None:
        return
    _showing = True
    try:
        QMessageBox.critical(
            None, "Непредвиденная ошибка",
            f"В приложении произошла ошибка:\n{exc}\n\n"
            f"Подробности записаны в журнал:\n{LOG_DIR}",
        )
    finally:
        _showing = False


def install_excepthook() -> None:
    """Установить глобальный обработчик исключений."""
    sys.excepthook = _handle_exception


__all__ = ["install_excepthook"]
