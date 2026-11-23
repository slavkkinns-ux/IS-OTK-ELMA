"""Слой бизнес-логики (Service Layer).

Все сервисы принимают репозитории через конструктор (dependency injection)
и содержат только бизнес-логику, без прямых SQL-запросов и работы с UI.
"""

from services.employee_service import EmployeeService
from services.client_service import ClientService
from services.order_service import OrderService
from services.service_service import ServiceService
from services.report_service import ReportService
from services.connection_service import ConnectionService

__all__ = [
    "EmployeeService",
    "ClientService",
    "OrderService",
    "ServiceService",
    "ReportService",
    "ConnectionService",
]
