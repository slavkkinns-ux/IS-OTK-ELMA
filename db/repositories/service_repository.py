"""Репозиторий услуг — CRUD для справочника услуг."""

from __future__ import annotations

from typing import Any

from db.repositories.base import AbstractRepository


class ServiceRepository(AbstractRepository):
    """Репозиторий услуг."""

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get_all_services(
        self, include_inactive: bool = False
    ) -> list[dict[str, Any]]:
        """Получить все услуги.

        Args:
            include_inactive: Если True, включать также отключённые услуги.
        """
        if include_inactive:
            query = """
                SELECT service_id, service_name, price, is_active
                FROM services
                ORDER BY service_name
            """
        else:
            query = """
                SELECT service_id, service_name, price, is_active
                FROM services
                WHERE is_active = 1
                ORDER BY service_name
            """
        return self.fetch_all(query)

    def service_name_exists(
        self, service_name: str, exclude_id: int | None = None
    ) -> bool:
        """Проверить, существует ли услуга с таким именем."""
        if exclude_id is not None:
            query = """
                SELECT 1 FROM services
                WHERE service_name = %s AND service_id <> %s
                LIMIT 1
            """
            row = self.fetch_one(query, (service_name, exclude_id))
        else:
            query = """
                SELECT 1 FROM services
                WHERE service_name = %s
                LIMIT 1
            """
            row = self.fetch_one(query, (service_name,))
        return row is not None

    def is_service_used(self, service_id: int) -> bool:
        """Проверить, используется ли услуга в заказах."""
        query = "SELECT 1 FROM order_services WHERE service_id = %s LIMIT 1"
        row = self.fetch_one(query, (service_id,))
        return row is not None

    # ------------------------------------------------------------------
    # Создание / обновление / удаление
    # ------------------------------------------------------------------

    def add_service(
        self, service_name: str, price: float
    ) -> int:
        """Добавить новую услугу. Возвращает service_id."""
        query = """
            INSERT INTO services (service_name, price, is_active)
            VALUES (%s, %s, 1)
        """
        return self.insert(query, (service_name, price))

    def update_service(
        self,
        service_id: int,
        service_name: str,
        price: float,
        is_active: int = 1,
    ) -> None:
        """Обновить услугу."""
        query = """
            UPDATE services
            SET service_name = %s, price = %s, is_active = %s
            WHERE service_id = %s
        """
        self.update(query, (service_name, price, is_active, service_id))

    def delete_service(self, service_id: int, soft: bool = True) -> None:
        """Удалить услугу.

        Args:
            service_id: ID услуги.
            soft: Если True — пометить неактивной (soft delete), если False — физическое удаление.
        """
        if soft:
            query = "UPDATE services SET is_active = 0 WHERE service_id = %s"
        else:
            query = "DELETE FROM services WHERE service_id = %s"
        self.update(query, (service_id,))


__all__ = ["ServiceRepository"]
