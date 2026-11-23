"""Функции форматирования значений для отображения."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def format_date(value: Any) -> str:
    """Безопасно форматировать дату или дату-время в строку ДД.ММ.ГГГГ."""
    if value is None:
        return ""
    if isinstance(value, (datetime, date)):
        return value.strftime("%d.%m.%Y")
    return str(value)


__all__ = ["format_date"]
