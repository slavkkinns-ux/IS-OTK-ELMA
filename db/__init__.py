"""Фасад доступа к базе данных (Data Access Layer).

Экспортирует:
- функции подключения: connect, get_connection, close
- экземпляр DatabaseConnection: db
- все репозитории: ClientRepository, OrderRepository, ServiceRepository,
  ReportRepository, EmployeeRepository
"""

from __future__ import annotations

from db.connection import (
    check_db,
    close_connection,
    connect_with_retry,
    ensure_columns,
    ensure_database,
    ensure_schema,
    get_config_info,
    get_last_error,
    is_db_available,
)
from db.database import DatabaseConnection, db
from db.repositories import (
    AbstractRepository,
    ClientRepository,
    EmployeeRepository,
    OrderRepository,
    ReportRepository,
    ServiceRepository,
)

# Экземпляры репозиториев для удобного импорта (один экземпляр на репозиторий)
client_repo = ClientRepository()
order_repo = OrderRepository()
services_repo = ServiceRepository()
report_repo = ReportRepository()
employee_repo = EmployeeRepository()

__all__ = [
    # Подключение
    "db",
    "DatabaseConnection",
    "connect",
    "get_connection",
    "close",
    # Схема / миграция
    "ensure_database",
    "ensure_schema",
    "ensure_columns",
    "check_db",
    "is_db_available",
    "connect_with_retry",
    "get_config_info",
    "get_last_error",
    "close_connection",
    # Репозитории (классы)
    "AbstractRepository",
    "ClientRepository",
    "OrderRepository",
    "ServiceRepository",
    "ReportRepository",
    "EmployeeRepository",
    # Репозитории (экземпляры)
    "client_repo",
    "order_repo",
    "services_repo",
    "report_repo",
    "employee_repo",
]


def connect():
    """Открыть соединение с БД."""
    return db.connect()


def get_connection():
    """Вернуть активное соединение."""
    return db.get_connection()


def close():
    """Закрыть соединение с БД."""
    db.close()
