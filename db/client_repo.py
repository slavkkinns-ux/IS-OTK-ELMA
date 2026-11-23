"""Репозиторий клиентов (обратная совместимость).

Все функции делегируют вызовы экземпляру ClientRepository.
"""

from __future__ import annotations

from typing import Any

from db.repositories.client_repository import ClientRepository

_client_repo = ClientRepository()


def get_all_clients() -> list[dict[str, Any]]:
    """Получить список всех активных клиентов."""
    return _client_repo.get_all_clients()


def get_clients_by_type(client_type: str) -> list[dict[str, Any]]:
    """Получить клиентов по типу (ЮЛ или ФЛ)."""
    return _client_repo.get_clients_by_type(client_type)


def get_client_by_id(client_id: int) -> dict[str, Any] | None:
    """Получить клиента по ID."""
    return _client_repo.get_client_by_id(client_id)


def get_client_details(client_id: int) -> dict[str, Any] | None:
    """Получить детали клиента (для просмотра/редактирования)."""
    return _client_repo.get_client_details(client_id)


def get_client_by_login(login: str, password_hash: str) -> dict[str, Any] | None:
    """Найти клиента по email или телефону и паролю (для авторизации)."""
    return _client_repo.get_client_by_login(login, password_hash)


def client_login_exists(login: str, exclude_id: int | None = None) -> bool:
    """Проверить, существует ли клиент с таким email или телефоном."""
    return _client_repo.client_login_exists(login, exclude_id)


def set_client_password(client_id: int, password_hash: str) -> None:
    """Установить пароль клиенту."""
    _client_repo.set_client_password(client_id, password_hash)


def get_clients_stats() -> dict[str, Any]:
    """Общая статистика по всем клиентам."""
    return _client_repo.get_clients_stats()


def get_client_stats(client_id: int) -> dict[str, Any]:
    """Статистика для конкретного клиента."""
    return _client_repo.get_client_stats(client_id)


def get_clients_orders_count() -> dict[int, int]:
    """Количество заказов по каждому клиенту."""
    return _client_repo.get_clients_orders_count()


def get_client_orders(client_id: int, limit: int | None = None) -> list[dict[str, Any]]:
    """Получить заказы клиента."""
    return _client_repo.get_client_orders(client_id, limit)


def get_client_reports(client_id: int) -> list[dict[str, Any]]:
    """Получить все отчёты клиента."""
    return _client_repo.get_client_reports(client_id)


def get_client_results(client_id: int) -> list[dict[str, Any]]:
    """Получить результаты исследований по всем заказам клиента."""
    return _client_repo.get_client_results(client_id)


def create_client(
    client_type: str,
    name: str,
    phone: str = "",
    email: str = "",
    password_hash: str = "",
    **kwargs: Any,
) -> int:
    """Создать нового клиента. Возвращает client_id."""
    return _client_repo.create_client(
        client_type=client_type,
        name=name,
        phone=phone,
        email=email,
        password_hash=password_hash,
        **kwargs,
    )


def update_client(
    client_id: int,
    client_type: str,
    name: str,
    phone: str = "",
    email: str = "",
    password_hash: str = "",
    **kwargs: Any,
) -> None:
    """Обновить данные клиента."""
    _client_repo.update_client(
        client_id=client_id,
        client_type=client_type,
        name=name,
        phone=phone,
        email=email,
        password_hash=password_hash,
        **kwargs,
    )


def add_client(data: dict[str, Any]) -> int:
    """Обёртка для client_dialog.py — принимает словарь."""
    return _client_repo.add_client(data)


def update_client_data(data: dict[str, Any]) -> None:
    """Обёртка для client_dialog.py — принимает словарь."""
    _client_repo.update_client_data(data)


get_client_info = get_client_by_id


__all__ = [
    "get_all_clients",
    "get_clients_by_type",
    "get_client_by_id",
    "get_client_details",
    "get_client_by_login",
    "client_login_exists",
    "set_client_password",
    "get_clients_stats",
    "get_client_stats",
    "get_clients_orders_count",
    "get_client_orders",
    "get_client_reports",
    "get_client_results",
    "create_client",
    "update_client",
    "add_client",
    "update_client_data",
    "get_client_info",
]
