"""Сервис услуг — бизнес-логика работы со справочником услуг."""

from __future__ import annotations

from typing import Any

from db.repositories.service_repository import ServiceRepository
from services.base_service import BaseService


class ServiceService(BaseService):
    """Сервис для управления услугами.

    Принимает репозиторий через конструктор (dependency injection).
    Не содержит прямых SQL-запросов и не зависит от UI.
    """

    def __init__(self, service_repo: ServiceRepository) -> None:
        self.repo = service_repo
        super().__init__()

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
        return self.repo.get_all_services(include_inactive=include_inactive)

    def service_name_exists(
        self, service_name: str, exclude_id: int | None = None
    ) -> bool:
        """Проверить, существует ли услуга с таким именем."""
        if not service_name or not service_name.strip():
            raise ValueError("Название услуги обязательно")
        return self.repo.service_name_exists(service_name.strip(), exclude_id)

    def is_service_used(self, service_id: int) -> bool:
        """Проверить, используется ли услуга в заказах."""
        if not isinstance(service_id, int) or service_id <= 0:
            raise ValueError(f"Некорректный ID услуги: {service_id}")
        return self.repo.is_service_used(service_id)

    # ------------------------------------------------------------------
    # Создание / обновление / удаление
    # ------------------------------------------------------------------

    def add_service(
        self, service_name: str, price: float
    ) -> int:
        """Добавить новую услугу с валидацией.

        Args:
            service_name: Название услуги (мин. 3 символа, уникальное).
            price: Цена услуги.

        Returns:
            ID созданной услуги.

        Raises:
            ValueError: При некорректных данных или дубле названия.
        """
        if not service_name or not service_name.strip():
            raise ValueError("Введите название услуги.")
        service_name = service_name.strip()

        if len(service_name) < 3:
            raise ValueError("Название должно содержать минимум 3 символа.")

        if self.repo.service_name_exists(service_name):
            raise ValueError(f"Услуга с названием «{service_name}» уже существует.")

        if price is None:
            raise ValueError("Введите цену.")
        try:
            price = float(price)
        except (ValueError, TypeError) as e:
            raise ValueError("Некорректный формат цены.") from e
        if price < 0:
            raise ValueError("Цена не может быть отрицательной.")

        service_id = self.repo.add_service(service_name, price)

        self.log_action("add_service", int(service_id), 0)
        return int(service_id)

    def update_service(
        self,
        service_id: int,
        service_name: str,
        price: float,
        is_active: int = 1,
    ) -> None:
        """Обновить услугу с валидацией.

        Args:
            service_id: ID услуги.
            service_name: Новое название.
            price: Новая цена.
            is_active: Активна ли услуга (1 или 0).
        """
        if not isinstance(service_id, int) or service_id <= 0:
            raise ValueError(f"Некорректный ID услуги: {service_id}")
        if not service_name or not service_name.strip():
            raise ValueError("Введите название услуги.")
        service_name = service_name.strip()

        if len(service_name) < 3:
            raise ValueError("Название должно содержать минимум 3 символа.")

        exclude_id = service_id
        if self.repo.service_name_exists(service_name, exclude_id=exclude_id):
            raise ValueError(f"Услуга с названием «{service_name}» уже существует.")

        try:
            price = float(price)
        except (ValueError, TypeError) as e:
            raise ValueError("Некорректный формат цены.") from e
        if price < 0:
            raise ValueError("Цена не может быть отрицательной.")

        self.repo.update_service(
            service_id=service_id,
            service_name=service_name,
            price=price,
            is_active=is_active,
        )

        self.log_action("update_service", service_id, 0)

    def delete_service(self, service_id: int, soft: bool = True) -> None:
        """Удалить услугу с проверкой использования.

        Args:
            service_id: ID услуги.
            soft: Если True — мягкое удаление (пометить неактивной).

        Raises:
            ValueError: Если услуга используется в заказах и soft=False.
        """
        if not isinstance(service_id, int) or service_id <= 0:
            raise ValueError(f"Некорректный ID услуги: {service_id}")

        if not soft:
            if self.repo.is_service_used(service_id):
                raise ValueError(
                    "Услуга используется в существующих заказах. "
                    "Невозможно физически удалить."
                )

        self.repo.delete_service(service_id=service_id, soft=soft)

        action = "soft_delete_service" if soft else "delete_service"
        self.log_action(action, service_id, 0)

    def toggle_service(self, service_id: int) -> int:
        """Переключить статус услуги (активна / отключена).

        Args:
            service_id: ID услуги.

        Returns:
            Новый статус is_active (1 или 0).
        """
        if not isinstance(service_id, int) or service_id <= 0:
            raise ValueError(f"Некорректный ID услуги: {service_id}")

        # Получаем текущий статус через репозиторий
        services = self.repo.get_all_services(include_inactive=True)
        current = next((s for s in services if int(s["service_id"]) == service_id), None)
        if not current:
            raise ValueError(f"Услуга с ID {service_id} не найдена")

        new_status = 0 if bool(current["is_active"]) else 1
        self.repo.update_service(
            service_id=service_id,
            service_name=str(current["service_name"]),
            price=float(current["price"]),
            is_active=new_status,
        )

        self.log_action("toggle_service", service_id, 0)
        return new_status


__all__ = ["ServiceService"]
