"""Сервис отчётов и исследований — бизнес-логика работы с отчётами."""

from __future__ import annotations

from typing import Any

from db.repositories.report_repository import ReportRepository
from db.repositories.order_repository import OrderRepository
from utils.files import open_file, print_file

from services.base_service import BaseService


class ReportService(BaseService):
    """Сервис для управления отчётами и исследованиями.

    Принимает репозитории через конструктор (dependency injection).
    Не содержит прямых SQL-запросов и не зависит от UI.
    """

    def __init__(
        self,
        report_repo: ReportRepository,
        order_repo: OrderRepository,
    ) -> None:
        self.report_repo = report_repo
        self.order_repo = order_repo
        super().__init__()

    # ------------------------------------------------------------------
    # Очередь исследований
    # ------------------------------------------------------------------

    def get_research_queue(self) -> list[dict[str, Any]]:
        """Получить очередь исследований (все услуги активных заказов)."""
        return self.report_repo.get_research_queue()

    def get_research_result(
        self, order_service_id: int
    ) -> dict[str, Any] | None:
        """Получить результат исследования по order_service_id."""
        if not isinstance(order_service_id, int) or order_service_id <= 0:
            raise ValueError(f"Некорректный ID услуги заказа: {order_service_id}")
        return self.report_repo.get_research_result(order_service_id)

    def save_research_result(
        self,
        order_service_id: int,
        employee_id: int,
        result_value: str,
        conclusion: str,
        result_date: Any,
    ) -> int:
        """Сохранить или обновить результат исследования.

        Returns:
            ID результата исследования.
        """
        if not isinstance(order_service_id, int) or order_service_id <= 0:
            raise ValueError(f"Некорректный ID услуги заказа: {order_service_id}")
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")

        research_id = self.report_repo.save_research_result(
            order_service_id, employee_id, result_value, conclusion, result_date
        )

        self.log_action("save_research_result", order_service_id, employee_id)
        return int(research_id)

    # ------------------------------------------------------------------
    # Исследования по заказу
    # ------------------------------------------------------------------

    def get_report_research(self, order_id: int) -> list[dict[str, Any]]:
        """Получить исследования по заказу (для отчёта)."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        return self.report_repo.get_report_research(order_id)

    # ------------------------------------------------------------------
    # Отчёты
    # ------------------------------------------------------------------

    def get_recent_reports(self, limit: int = 10) -> list[dict[str, Any]]:
        """Получить последние отчёты."""
        if not isinstance(limit, int) or limit <= 0:
            raise ValueError(f"Некорректный лимит: {limit}")
        return self.report_repo.get_recent_reports(limit)

    def get_report(self, report_id: int) -> dict[str, Any] | None:
        """Получить данные отчёта по ID."""
        if not isinstance(report_id, int) or report_id <= 0:
            raise ValueError(f"Некорректный ID отчёта: {report_id}")
        return self.report_repo.get_report(report_id)

    def get_report_by_order(self, order_id: int) -> dict[str, Any] | None:
        """Получить последний отчёт по заказу (для проверки дубликата)."""
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        return self.report_repo.get_report_by_order(order_id)

    def create_report(
        self, order_id: int, employee_id: int, file_path: str | None = None
    ) -> int:
        """Создать запись отчёта в БД.

        Args:
            order_id: ID заказа.
            employee_id: ID сотрудника.
            file_path: Путь к PDF. Может быть None: запись создаётся до генерации
                файла, путь затем задаётся через update_report_path.

        Returns:
            ID созданного отчёта.
        """
        if not isinstance(order_id, int) or order_id <= 0:
            raise ValueError(f"Некорректный ID заказа: {order_id}")
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")

        report_id = self.report_repo.create_report(order_id, employee_id, file_path)

        self.log_action("create_report", int(report_id), employee_id)
        return int(report_id)

    def get_next_report_number(self) -> int:
        """Получить следующий номер отчёта."""
        return self.report_repo.get_next_report_number()

    def get_report_by_path(self, file_path: str) -> dict[str, Any] | None:
        """Найти отчёт по пути к файлу."""
        if not file_path:
            raise ValueError("Путь к файлу обязателен")
        return self.report_repo.get_report_by_path(file_path)

    def delete_report(self, report_id: int) -> None:
        """Удалить отчёт из базы данных."""
        if not isinstance(report_id, int) or report_id <= 0:
            raise ValueError(f"Некорректный ID отчёта: {report_id}")
        self.report_repo.delete_report(report_id)

        self.log_action("delete_report", report_id, 0)

    def update_report_path(self, report_id: int, file_path: str) -> None:
        """Обновить путь к файлу отчёта."""
        if not isinstance(report_id, int) or report_id <= 0:
            raise ValueError(f"Некорректный ID отчёта: {report_id}")
        if not file_path:
            raise ValueError("Путь к файлу обязателен")
        self.report_repo.update_report_path(report_id, file_path)

    # ------------------------------------------------------------------
    # Открытие / печать PDF (вспомогательные методы, без SQL)
    # ------------------------------------------------------------------

    def open_file(self, file_path: str) -> None:
        """Открыть файл в системном приложении."""
        try:
            open_file(file_path)
        except Exception as exc:
            self.logger.error("Не удалось открыть файл %s: %s", file_path, exc)
            raise

    def print_file(self, file_path: str) -> None:
        """Отправить файл на печать."""
        try:
            print_file(file_path)
        except Exception as exc:
            self.logger.error("Не удалось отправить на печать %s: %s", file_path, exc)
            raise


__all__ = ["ReportService"]
