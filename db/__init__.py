"""Фасад доступа к базе данных."""
from repositories.base_repository import BaseRepository
from repositories.client_repository import ClientRepository
from repositories.order_repository import OrderRepository
from repositories.report_repository import ReportRepository
from db.connection import connection_manager, get_connection, close_connection

# Создаём экземпляры репозиториев
base_repo = BaseRepository()
client_repo = ClientRepository()
order_repo = OrderRepository()
report_repo = ReportRepository()


def connect():
    """Инициализировать соединение с БД."""
    connection_manager.get_connection()


def close():
    """Закрыть соединение с БД."""
    connection_manager.close()


__all__ = [
    'base_repo',
    'client_repo',
    'order_repo',
    'report_repo',
    'connect',
    'close',
    'get_connection',
    'close_connection',
]