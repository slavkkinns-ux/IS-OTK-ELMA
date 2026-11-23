"""Сервис клиентов — бизнес-логика работы с клиентами."""

from __future__ import annotations

import hashlib
from typing import Any

from db.repositories.client_repository import ClientRepository

from services.base_service import BaseService


class ClientService(BaseService):
    """Сервис для управления клиентами.

    Принимает репозиторий через конструктор (dependency injection).
    Не содержит прямых SQL-запросов и не зависит от UI.
    """

    def __init__(self, client_repo: ClientRepository) -> None:
        self.repo = client_repo
        super().__init__()

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get_all_clients(self) -> list[dict[str, Any]]:
        """Получить список всех активных клиентов."""
        return self.repo.get_all_clients()

    def get_clients_by_type(self, client_type: str) -> list[dict[str, Any]]:
        """Получить клиентов по типу ('ЮЛ' или 'ФЛ')."""
        if not client_type or client_type not in ("ЮЛ", "ФЛ"):
            raise ValueError(f"Некорректный тип клиента: {client_type}")
        return self.repo.get_clients_by_type(client_type)

    def get_client_by_id(self, client_id: int) -> dict[str, Any] | None:
        """Получить клиента по ID."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_by_id(client_id)

    def get_client_details(self, client_id: int) -> dict[str, Any] | None:
        """Получить детальную информацию о клиенте."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_details(client_id)

    def get_client_stats(self, client_id: int) -> dict[str, Any]:
        """Получить статистику клиента."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_stats(client_id)

    def get_clients_stats(self) -> dict[str, Any]:
        """Получить общую статистику по клиентам."""
        return self.repo.get_clients_stats()

    def get_clients_orders_count(self) -> dict[int, int]:
        """Получить количество заказов по каждому клиенту."""
        return self.repo.get_clients_orders_count()

    # ------------------------------------------------------------------
    # Заказы, отчёты, результаты клиента
    # ------------------------------------------------------------------

    def get_client_orders(
        self, client_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Получить заказы клиента."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_orders(client_id, limit)

    def get_client_reports(self, client_id: int) -> list[dict[str, Any]]:
        """Получить все отчёты клиента."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_reports(client_id)

    def get_client_results(self, client_id: int) -> list[dict[str, Any]]:
        """Получить результаты исследований клиента."""
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        return self.repo.get_client_results(client_id)

    # ------------------------------------------------------------------
    # Авторизация клиента
    # ------------------------------------------------------------------

    def authenticate_client(
        self, login: str, password: str
    ) -> dict[str, Any] | None:
        """Аутентифицировать клиента по логину (email/телефон) и паролю.

        Args:
            login: Email или телефон клиента.
            password: Пароль в открытом виде.

        Returns:
            Данные клиента или None, если аутентификация не удалась.
        """
        if not login or not login.strip():
            raise ValueError("Логин обязателен")
        if not password:
            raise ValueError("Пароль обязателен")

        login = login.strip()
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        client = self.repo.get_client_by_login(login, password_hash)
        if client:
            self.logger.info("Клиент авторизован: id=%s, login=%s", client.get("client_id"), login)
        return client

    def client_login_exists(
        self, login: str, exclude_id: int | None = None
    ) -> bool:
        """Проверить, существует ли клиент с таким email или телефоном."""
        if not login:
            raise ValueError("Логин обязателен")
        return self.repo.client_login_exists(login, exclude_id)

    # ------------------------------------------------------------------
    # Создание / обновление
    # ------------------------------------------------------------------

    def create_client(
        self,
        client_type: str,
        name: str,
        phone: str = "",
        email: str = "",
        password: str = "",
        **kwargs: Any,
    ) -> int:
        """Создать нового клиента с валидацией.

        Args:
            client_type: Тип клиента ('ЮЛ' или 'ФЛ').
            name: Название компании или ФИО.
            phone: Телефон.
            email: Email.
            password: Пароль для входа клиента (открытый текст).
            **kwargs: Дополнительные поля (address, inn, kpp и т.д.).

        Returns:
            ID созданного клиента.

        Raises:
            ValueError: При некорректных данных или отсутствии email/телефона.
        """
        if not client_type or client_type not in ("ЮЛ", "ФЛ"):
            raise ValueError(f"Некорректный тип клиента: {client_type}")
        if not name or not name.strip():
            raise ValueError("Название / ФИО обязательно для заполнения")
        name = name.strip()

        if not email and not phone:
            raise ValueError("Укажите E-mail или телефон для входа.")

        if not password:
            raise ValueError("Пароль обязателен для входа клиента.")

        password_hash = hashlib.sha256(password.encode()).hexdigest()

        client_id = self.repo.create_client(
            client_type=client_type,
            name=name,
            phone=phone,
            email=email,
            password_hash=password_hash,
            **kwargs,
        )

        self.log_action("create_client", int(client_id), 0)
        return int(client_id)

    def update_client(
        self,
        client_id: int,
        client_type: str,
        name: str,
        phone: str = "",
        email: str = "",
        password: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Обновить данные клиента.

        Args:
            client_id: ID клиента.
            client_type: Тип клиента ('ЮЛ' или 'ФЛ').
            name: Название компании или ФИО.
            phone: Телефон.
            email: Email.
            password: Новый пароль (если None — не менять).
            **kwargs: Дополнительные поля.
        """
        if not isinstance(client_id, int) or client_id <= 0:
            raise ValueError(f"Некорректный ID клиента: {client_id}")
        if not client_type or client_type not in ("ЮЛ", "ФЛ"):
            raise ValueError(f"Некорректный тип клиента: {client_type}")
        if not name or not name.strip():
            raise ValueError("Название / ФИО обязательно для заполнения")
        name = name.strip()

        password_hash = None
        if password:
            password_hash = hashlib.sha256(password.encode()).hexdigest()

        self.repo.update_client(
            client_id=client_id,
            client_type=client_type,
            name=name,
            phone=phone,
            email=email,
            password_hash=password_hash,
            **kwargs,
        )

        self.log_action("update_client", client_id, 0)


__all__ = ["ClientService"]
