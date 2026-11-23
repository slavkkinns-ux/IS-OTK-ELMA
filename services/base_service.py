"""Базовый класс сервисов: общий логгер и журнал действий."""

from __future__ import annotations

import logging


class BaseService:
    """Даёт сервису логгер модуля и метод log_action (раньше он был скопирован в 6 сервисов)."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(type(self).__module__)

    def log_action(
        self,
        action: str,
        target_id: int,
        employee_id: int | None = None,
        details: str = "",
    ) -> None:
        """Записать действие пользователя в лог (уровень INFO).

        Args:
            action: Название действия (например, 'deactivate_employee').
            target_id: ID объекта, над которым выполнено действие.
            employee_id: ID пользователя. Если не указан (None или 0), в записи
                будет «Пользователь не указан».
            details: Дополнительные подробности.
        """
        actor = f"Пользователь {employee_id}" if employee_id else "Пользователь не указан"
        msg = f"{actor} выполнил '{action}' над объектом {target_id}"
        if details:
            msg += f" ({details})"
        self.logger.info(msg)


__all__ = ["BaseService"]
