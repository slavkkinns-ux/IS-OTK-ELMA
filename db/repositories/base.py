"""Базовый класс для всех репозиториев доступа к данным.

Предоставляет общий доступ к экземпляру DatabaseConnection и типобезопасные
обёртки над методами выполнения SQL-запросов.
"""

from __future__ import annotations

from typing import Any

from db.database import db


class AbstractRepository:
    """Базовый класс репозитория.

    Все конкретные репозитории наследуются от этого класса и получают
    доступ к общему экземпляру соединения с базой данных через self.db.
    """

    def __init__(self) -> None:
        self.db = db

    # ------------------------------------------------------------------
    # SELECT
    # ------------------------------------------------------------------

    def fetch_all(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """Выполнить SELECT-запрос и вернуть список словарей."""
        return self.db.execute_query(query, params)

    def fetch_one(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> dict[str, Any] | None:
        """Выполнить SELECT-запрос и вернуть одну строку или None."""
        return self.db.execute_fetchone(query, params)

    # ------------------------------------------------------------------
    # INSERT / UPDATE / DELETE
    # ------------------------------------------------------------------

    def insert(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> int:
        """Выполнить INSERT и вернуть ID новой строки."""
        return self.db.execute_insert(query, params)

    def update(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> int:
        """Выполнить UPDATE/DELETE и вернуть количество затронутых строк."""
        return self.db.execute_update(query, params)

    def insert_many(
        self, query: str, params_list: list[tuple[Any, ...]]
    ) -> int:
        """Выполнить запрос с набором параметров (executemany)."""
        return self.db.execute_many(query, params_list)

    # ------------------------------------------------------------------
    # Транзакции
    # ------------------------------------------------------------------

    def transaction(self) -> Any:
        """Контекстный менеджер транзакции.

        Использование:
            with self.repository.transaction() as conn:
                ...
        """
        return self.db.transaction()


__all__ = ["AbstractRepository"]
