"""Доступ к соединению с MySQL для репозиториев.

DatabaseConnection не хранит собственное соединение: он использует единое
соединение из db.connection. Раньше их было два (одно в ConnectionDialog,
другое в репозиториях), и закрытие одного не затрагивало другое.
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

import pymysql

from db import connection as _conn

logger = logging.getLogger(__name__)


class DatabaseConnection:
    """Выполнение запросов и транзакций поверх общего соединения.

    - Перед каждой операцией соединение проверяется (ping) и при обрыве
      восстанавливается.
    - После чтения выполняется commit, чтобы закрыть снимок данных (MySQL
      REPEATABLE READ): иначе долгоживущее соединение не видит чужих изменений.
    - При ошибке записи выполняется rollback, чтобы не оставить открытую транзакцию.
    """

    # ------------------------------------------------------------------
    # Подключение
    # ------------------------------------------------------------------

    def connect(self) -> Any:
        """Установить соединение с БД (или проверить существующее)."""
        return _conn.get_connection()

    def get_connection(self) -> Any:
        """Вернуть рабочее соединение (при обрыве переподключается)."""
        return _conn.get_connection()

    def close(self) -> None:
        """Закрыть соединение с БД."""
        _conn.close_connection()

    def is_available(self) -> bool:
        """Проверить доступность БД."""
        return _conn.is_db_available()

    def connect_with_retry(self, max_attempts: int = 3, delay: float = 1.0) -> bool:
        """Подключиться с повторными попытками."""
        return _conn.connect_with_retry(max_attempts=max_attempts, delay=delay)

    def ensure_schema(self) -> str:
        """Выполнить полную проверку и миграцию схемы БД."""
        return _conn.ensure_schema()

    def get_config_info(self) -> str:
        """Вернуть информацию о конфигурации подключения."""
        return _conn.get_config_info()

    def get_last_error(self) -> str | None:
        """Вернуть текст последней ошибки подключения."""
        return _conn.get_last_error()

    # ------------------------------------------------------------------
    # Вспомогательные
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_rollback(conn: Any) -> None:
        try:
            conn.rollback()
        except pymysql.MySQLError as exc:
            logger.warning("Не удалось откатить транзакцию: %s", exc)

    @staticmethod
    def _end_read(conn: Any) -> None:
        """Закрыть снимок чтения. Ошибку здесь не пробрасываем, чтобы не скрыть исходную."""
        try:
            conn.commit()
        except pymysql.MySQLError as exc:
            logger.warning("Не удалось завершить чтение: %s", exc)

    @contextmanager
    def _read_cursor(self) -> Iterator[Any]:
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                yield cur
        finally:
            self._end_read(conn)

    @contextmanager
    def _write_cursor(self) -> Iterator[Any]:
        conn = self.get_connection()
        try:
            with conn.cursor() as cur:
                yield cur
            conn.commit()
        except Exception as exc:
            logger.warning("Запись отменена: %s", exc)
            self._safe_rollback(conn)
            raise

    # ------------------------------------------------------------------
    # Выполнение запросов
    # ------------------------------------------------------------------

    def execute_query(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> list[dict[str, Any]]:
        """Выполнить SELECT и вернуть список словарей."""
        with self._read_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()

    def execute_fetchone(
        self, query: str, params: tuple[Any, ...] | None = None
    ) -> dict[str, Any] | None:
        """Выполнить SELECT и вернуть одну строку (или None)."""
        with self._read_cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchone()

    def execute_insert(self, query: str, params: tuple[Any, ...] | None = None) -> int:
        """Выполнить INSERT и вернуть ID новой строки."""
        with self._write_cursor() as cur:
            cur.execute(query, params or ())
            last_id = cur.lastrowid
        return int(last_id) if last_id is not None else 0

    def execute_update(self, query: str, params: tuple[Any, ...] | None = None) -> int:
        """Выполнить UPDATE/DELETE и вернуть число затронутых строк."""
        with self._write_cursor() as cur:
            cur.execute(query, params or ())
            affected = cur.rowcount
        return int(affected)

    def execute_many(self, query: str, params_list: list[tuple[Any, ...]]) -> int:
        """Выполнить запрос с набором параметров (executemany)."""
        with self._write_cursor() as cur:
            cur.executemany(query, params_list)
            affected = cur.rowcount
        return int(affected)

    # ------------------------------------------------------------------
    # Транзакции
    # ------------------------------------------------------------------

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """Транзакция: commit при успехе, rollback при исключении."""
        conn = self.get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as exc:
            logger.warning("Транзакция отменена: %s", exc)
            self._safe_rollback(conn)
            raise


# Глобальный экземпляр
db = DatabaseConnection()

__all__ = ["DatabaseConnection", "db"]
