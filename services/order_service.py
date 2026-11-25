"""Сервис заказов — бизнес-логика работы с заказами."""

from __future__ import annotations

from typing import Any

from db.repositories.client_repository import ClientRepository
from db.repositories.order_repository import OrderRepository
from db.repositories.service_repository import ServiceRepository
from services.base_service import BaseService


class OrderService(BaseService):
    """Сервис для управления заказами.

    Принимает репозитории через конструктор (dependency injection).
    Не содержит прямых SQL-запросов и не зависит от UI.
    """

    def __init__(
        self,
        order_repo: OrderRepository,
        client_repo: ClientRepository,
        service_repo: ServiceRepository,
    ) -> None:
        self.order_repo = order_repo
        self.client_repo = client_repo
        self.service_repo = service_repo
        super().__init__()

    # ------------------------------------------------------------------
    # Чтение заказов
    # ------------------------------------------------------------------

    def get_all_orders(self) -> list[dict[str, Any]]:
        """Получить все заказы."""
        return self.order_repo.get_all_orders()

    def get_order(self, order_id: int) -> dict[str, Any] | None:
        """Получить заказ по ID с данными клиента и сотрудника."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        return self.order_repo.get_order(order_id)

    def get_order_services(self, order_id: int) -> list[dict[str, Any]]:
        """Получить услуги заказа с ценами на момент заказа."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        return self.order_repo.get_order_services(order_id)

    def get_active_services(self) -> list[dict[str, Any]]:
        """Получить список активных услуг для выбора при создании заказа."""
        return self.order_repo.get_active_services()

    def search_orders(self, query: str) -> list[dict[str, Any]]:
        """Поиск заказов по коду сосуда, клиенту, статусу."""
        if not query or not query.strip():
            raise ValueError("Поисковой запрос обязателен")
        return self.order_repo.search_orders(query.strip())

    def get_orders_stats(self) -> dict[str, Any]:
        """Получить статистику заказов по статусам."""
        return self.order_repo.get_orders_stats()

    def get_home_stats(self) -> dict[str, Any]:
        """Получить статистику для главной страницы."""
        return self.order_repo.get_home_stats()

    def get_recent_orders(self, limit: int = 5) -> list[dict[str, Any]]:
        """Получить последние заказы."""
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Некорректный лимит: {limit}")
        return self.order_repo.get_recent_orders(limit)

    # ------------------------------------------------------------------
    # Код сосуда
    # ------------------------------------------------------------------

    def get_next_vessel_code(self) -> str:
        """Сгенерировать следующий код лабораторного сосуда."""
        return self.order_repo.get_next_vessel_code()

    def vessel_code_exists(
        self,
        code: str,
        exclude_archived: bool = True,
        exclude_order_id: int | None = None,
    ) -> bool:
        """Проверить, существует ли уже заказ с таким кодом сосуда."""
        if not code or not code.strip():
            raise ValueError("Код сосуда обязателен")
        return self.order_repo.vessel_code_exists(
            code.strip(),
            exclude_archived=exclude_archived,
            exclude_order_id=exclude_order_id,
        )

    # ------------------------------------------------------------------
    # Клиенты для заказа
    # ------------------------------------------------------------------

    def get_clients_by_type(self, client_type: str) -> list[dict[str, Any]]:
        """Получить клиентов по типу для выпадающего списка заказа."""
        return self.client_repo.get_clients_by_type(client_type)

    # ------------------------------------------------------------------
    # Создание / обновление заказа
    # ------------------------------------------------------------------

    def create_order(
        self,
        vessel_code: str,
        client_id: int,
        employee_id: int,
        service_ids: list[int],
        total_price: float,
    ) -> int:
        """Создать новый заказ с валидацией.

        Args:
            vessel_code: Код лабораторного сосуда.
            client_id: ID клиента.
            employee_id: ID сотрудника.
            service_ids: Список ID выбранных услуг.
            total_price: Итоговая стоимость.

        Returns:
            ID созданного заказа.

        Raises:
            ValueError: При некорректных данных или дубликате кода сосуда.
        """
        if not vessel_code or not vessel_code.strip():
            raise ValueError("Код сосуда обязателен")
        vessel_code = vessel_code.strip()

        if self.order_repo.vessel_code_exists(vessel_code, exclude_archived=True):
            raise ValueError(f"Код сосуда '{vessel_code}' уже используется в активных заказах")

        if not client_id or client_id <= 0:
            raise ValueError("Клиент обязателен")
        if not employee_id or employee_id <= 0:
            raise ValueError("Сотрудник обязателен")
        if not service_ids:
            raise ValueError("Выберите хотя бы одну услугу")

        order_id = self.order_repo.create_order(
            vessel_code=vessel_code,
            client_id=client_id,
            employee_id=employee_id,
            service_ids=service_ids,
            total_price=total_price,
        )

        self.log_action("create_order", int(order_id), employee_id)
        return int(order_id)

    def update_order(
        self,
        order_id: int,
        vessel_code: str,
        client_id: int,
        employee_id: int,
        service_ids: list[int],
        total_price: float,
    ) -> None:
        """Обновить существующий заказ с валидацией.

        Args:
            order_id: ID заказа.
            vessel_code: Код лабораторного сосуда.
            client_id: ID клиента.
            employee_id: ID сотрудника.
            service_ids: Список ID выбранных услуг.
            total_price: Итоговая стоимость.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        if not vessel_code or not vessel_code.strip():
            raise ValueError("Код сосуда обязателен")
        vessel_code = vessel_code.strip()

        if self.order_repo.vessel_code_exists(
            vessel_code, exclude_archived=True, exclude_order_id=order_id
        ):
            raise ValueError(
                f"Код сосуда '{vessel_code}' уже используется в активных заказах"
            )

        if not client_id or client_id <= 0:
            raise ValueError("Клиент обязателен")
        if not employee_id or employee_id <= 0:
            raise ValueError("Сотрудник обязателен")
        if not service_ids:
            raise ValueError("Выберите хотя бы одну услугу")

        self.order_repo.update_order(
            order_id=order_id,
            vessel_code=vessel_code,
            client_id=client_id,
            employee_id=employee_id,
            service_ids=service_ids,
            total_price=total_price,
        )

        self.log_action("update_order", order_id, employee_id)


__all__ = ["OrderService"]
