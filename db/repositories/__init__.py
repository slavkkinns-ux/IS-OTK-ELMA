"""Пакет репозиториев доступа к данным (Data Access Layer).

Экспортирует все репозитории приложения для удобного импорта.
"""

from db.repositories.base import AbstractRepository
from db.repositories.client_repository import ClientRepository
from db.repositories.employee_repository import EmployeeRepository
from db.repositories.order_repository import OrderRepository
from db.repositories.report_repository import ReportRepository
from db.repositories.service_repository import ServiceRepository

__all__ = [
    "AbstractRepository",
    "ClientRepository",
    "OrderRepository",
    "ServiceRepository",
    "ReportRepository",
    "EmployeeRepository",
]
