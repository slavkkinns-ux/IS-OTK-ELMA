"""Репозиторий заказов (обратная совместимость).

Все функции deleгируют вызовы экземпляру OrderRepository.
"""

from __future__ import annotations

from typing import Any

from db.repositories.order_repository import OrderRepository

_order_repo = OrderRepository()


def get_active_services() -> list[dict[str, Any]]:
    """Получить список активных услуг."""
    return _order_repo.get_active_services()


def get_order(order_id: int) -> dict[str, Any] | None:
    """Полная карточка заказа."""
    return _order_repo.get_order(order_id)


def get_order_services(order_id: int) -> list[dict[str, Any]]:
    """Получить услуги заказа с ценами на момент заказа."""
    return _order_repo.get_order_services(order_id)


def get_next_vessel_code() -> str:
    """Сгенерировать следующий код лабораторного сосуда."""
    return _order_repo.get_next_vessel_code()


def vessel_code_exists(
    code: str,
    exclude_archived: bool = True,
    exclude_order_id: int | None = None,
) -> bool:
    """Проверить дубликат кода сосуда."""
    return _order_repo.vessel_code_exists(
        code, exclude_archived=exclude_archived, exclude_order_id=exclude_order_id
    )


def create_order(
    vessel_code: str,
    client_id: int,
    employee_id: int,
    service_ids: list[int],
    total_price: float,
) -> int:
    """Создать заказ. Возвращает order_id."""
    return _order_repo.create_order(
        vessel_code=vessel_code,
        client_id=client_id,
        employee_id=employee_id,
        service_ids=service_ids,
        total_price=total_price,
    )


def update_order(
    order_id: int,
    vessel_code: str,
    client_id: int,
    employee_id: int,
    service_ids: list[int],
    total_price: float,
) -> None:
    """Обновить заказ."""
    _order_repo.update_order(
        order_id=order_id,
        vessel_code=vessel_code,
        client_id=client_id,
        employee_id=employee_id,
        service_ids=service_ids,
        total_price=total_price,
    )


def search_orders(query: str) -> list[dict[str, Any]]:
    """Поиск заказов."""
    return _order_repo.search_orders(query)


def get_all_orders() -> list[dict[str, Any]]:
    """Получить все заказы."""
    return _order_repo.get_all_orders()


def get_orders_stats() -> dict[str, Any]:
    """Статистика заказов по статусам."""
    return _order_repo.get_orders_stats()


def get_home_stats() -> dict[str, Any]:
    """Статистика для главной страницы."""
    return _order_repo.get_home_stats()


def get_recent_orders(limit: int = 5) -> list[dict[str, Any]]:
    """Получить последние заказы."""
    return _order_repo.get_recent_orders(limit)


__all__ = [
    "get_active_services",
    "get_order",
    "get_order_services",
    "get_next_vessel_code",
    "vessel_code_exists",
    "create_order",
    "update_order",
    "search_orders",
    "get_all_orders",
    "get_orders_stats",
    "get_home_stats",
    "get_recent_orders",
]
