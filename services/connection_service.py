"""Сервис подключения к базе данных — инфраструктурный слой.

Инкапсулирует работу с db.connection: проверка доступности, подключение,
миграция схемы, получение информации о конфигурации.
"""

from __future__ import annotations

import logging
from typing import Any

from db.connection import (
    connect as _connect,
    get_config_info as _get_config_info,
    ensure_schema as _ensure_schema,
    check_db as _check_db,
    connect_with_retry as _connect_with_retry,
    close_connection as _close_connection,
)


class ConnectionService:
    """Сервис для управления подключением к MySQL.

    Не содержит бизнес-логики — только инфраструктурные операции с БД.
    """

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    def is_db_available(self) -> bool:
        """Проверить доступность базы данных."""
        ok, _ = _check_db()
        return ok

    def check_db(self) -> tuple[bool, str | None]:
        """Прокаверять доступность БД с деталями ошибки."""
        return _check_db()

    def connect(self) -> Any:  # type: ignore[name-defined]
        """Установить соединение с базой данных."""
        return _connect()

    def get_config_info(self) -> str:
        """Вернуть информацию о текущей конфигурации подключения."""
        return _get_config_info()

    def ensure_schema(self) -> str:
        """Выполнить полную проверку и миграцию схемы БД."""
        return _ensure_schema()

    def connect_with_retry(
        self, max_attempts: int = 3, delay: float = 1.0
    ) -> bool:
        """Попытаться подключиться с повторными попытками."""
        return _connect_with_retry(max_attempts=max_attempts, delay=delay)

    def close(self) -> None:
        """Закрыть соединение с базой данных."""
        _close_connection()


__all__ = ["ConnectionService"]
