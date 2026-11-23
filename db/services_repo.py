"""Репозиторий услуг (обратная совместимость).

Все функции deleгируют вызовы экземпляру ServiceRepository.
"""

from __future__ import annotations

from typing import Any

from db.repositories.service_repository import ServiceRepository

_service_repo = ServiceRepository()


def get_all_services(include_inactive: bool = False) -> list[dict[str, Any]]:
    """Получить все услуги."""
    return _service_repo.get_all_services(include_inactive=include_inactive)


def add_service(service_name: str, price: float) -> int:
    """Добавить новую услугу. Возвращает service_id."""
    return _service_repo.add_service(service_name, price)


def update_service(
    service_id: int,
    service_name: str,
    price: float,
    is_active: int = 1,
) -> None:
    """Обновить услугу."""
    _service_repo.update_service(
        service_id=service_id,
        service_name=service_name,
        price=price,
        is_active=is_active,
    )


def delete_service(service_id: int, soft: bool = True) -> None:
    """Удалить услугу. soft=True — пометить неактивной."""
    _service_repo.delete_service(service_id=service_id, soft=soft)


def service_name_exists(
    service_name: str, exclude_id: int | None = None
) -> bool:
    """Проверить, существует ли услуга с таким именем."""
    return _service_repo.service_name_exists(service_name, exclude_id=exclude_id)


def is_service_used(service_id: int) -> bool:
    """Проверить, используется ли услуга в заказах."""
    return _service_repo.is_service_used(service_id)


__all__ = [
    "get_all_services",
    "add_service",
    "update_service",
    "delete_service",
    "service_name_exists",
    "is_service_used",
]
