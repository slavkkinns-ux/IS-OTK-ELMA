"""Репозитории доступа к базе данных."""

from repositories.base_repository import BaseRepository
from repositories.client_repository import ClientRepository
from repositories.order_repository import OrderRepository
from repositories.report_repository import ReportRepository

__all__ = [
    "BaseRepository",
    "ClientRepository",
    "OrderRepository",
    "ReportRepository",
]
