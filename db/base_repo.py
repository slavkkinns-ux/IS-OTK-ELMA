"""Базовые функции для работы с базой данных (обратная совместимость).

Все функции делегируют вызовы экземпляру DatabaseConnection и репозиториям.
Используется в модулях'autorзации и других местах, где нужны низкоуровневые запросы.
"""

from __future__ import annotations

from typing import Any

from db.database import db


def connect():
    """Открыть соединение с базой данных."""
    return db.connect()


def get_connection():
    """Вернуть активное соединение."""
    return db.get_connection()


def execute_query(query: str, params=None) -> list[dict[str, Any]]:
    """Выполнить SQL-запрос (SELECT) и вернуть список словарей."""
    return db.execute_query(query, params or ())


def execute_insert(query: str, params=None) -> int:
    """Выполнить INSERT и вернуть ID новой строки."""
    return db.execute_insert(query, params or ())


def close():
    """Закрыть соединение с базой данных."""
    db.close()


__all__ = ["connect", "get_connection", "execute_query", "execute_insert", "close"]
