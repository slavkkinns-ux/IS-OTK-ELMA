from db.connection import get_connection
import logging

logger = logging.getLogger(__name__)


class BaseRepository:
    """Базовый класс для всех репозиториев."""

    def execute_query(self, query: str, params: tuple = None) -> list:
        """Выполняет SELECT и возвращает список словарей."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                return cursor.fetchall()
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}\nQuery: {query}")
            raise

    def execute_insert(self, query: str, params: tuple = None) -> int:
        """Выполняет INSERT и возвращает lastrowid."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.lastrowid
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка вставки: {e}\nQuery: {query}")
            raise

    def execute_update(self, query: str, params: tuple = None) -> int:
        """Выполняет UPDATE и возвращает количество изменённых строк."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка обновления: {e}\nQuery: {query}")
            raise

    def execute_delete(self, query: str, params: tuple = None) -> int:
        """Выполняет DELETE и возвращает количество удалённых строк."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                conn.commit()
                return cursor.rowcount
        except Exception as e:
            conn.rollback()
            logger.error(f"Ошибка удаления: {e}\nQuery: {query}")
            raise