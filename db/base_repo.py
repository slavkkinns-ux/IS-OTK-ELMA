"""Базовые функции для работы с базой данных.
Используется в модулях авторизации и других местах, где нужны низкоуровневые запросы.
"""
from db.connection import get_connection as _db_get_connection


def connect():
    """Открывает соединение с базой данных."""
    return _db_get_connection()


def get_connection():
    """Возвращает активное соединение."""
    return _db_get_connection()


def execute_query(query: str, params=None) -> list[dict]:
    """Выполняет SQL-запрос (SELECT) и возвращает список словарей."""
    conn = _db_get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            return cur.fetchall()
    finally:
        conn.close()


def execute_insert(query: str, params=None) -> int:
    """Выполняет INSERT и возвращает ID новой строки."""
    conn = _db_get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
            return cur.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def close():
    """Закрывает соединение с базой данных."""
    from db.connection import close_connection
    close_connection()