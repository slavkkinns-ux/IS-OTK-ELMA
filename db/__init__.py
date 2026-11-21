"""Фасад доступа к базе данных."""
from db import connection
from db import client_repo
from db import order_repo
from db import services_repo

try:
    from db import report_repo
except ImportError:
    report_repo = None


def connect():
    """Открывает соединение с БД."""
    return connection.get_connection()


def get_connection():
    """Возвращает активное соединение."""
    return connection.get_connection()


def close():
    """Закрывает соединение с БД."""
    connection.close_connection()


__all__ = [
    'connect', 'get_connection', 'close',
    'client_repo', 'order_repo', 'services_repo', 'report_repo',
]