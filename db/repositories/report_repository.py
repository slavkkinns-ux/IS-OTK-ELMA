"""Репозиторий отчётов и исследований — доступ к данным об исследованиях и отчётах."""

from __future__ import annotations

from typing import Any

from db.repositories.base import AbstractRepository


class ReportRepository(AbstractRepository):
    """Репозиторий отчётов и результатов исследований."""

    # ------------------------------------------------------------------
    # Очередь исследований
    # ------------------------------------------------------------------

    def get_research_queue(self) -> list[dict[str, Any]]:
        """Очередь исследований (все услуги активных заказов)."""
        query = """
            SELECT
                os.order_service_id,
                o.order_id,
                o.vessel_code,
                s.service_name,
                CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                     ELSE i.full_name END AS client_name,
                rr.result_value
            FROM order_services os
            JOIN orders o ON o.order_id = os.order_id
            JOIN services s ON s.service_id = os.service_id
            JOIN clients c ON c.client_id = o.client_id
            LEFT JOIN legal_entities le
                ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
            LEFT JOIN individuals i
                ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
            LEFT JOIN research_results rr
                ON rr.order_service_id = os.order_service_id
            WHERE o.status NOT IN ('Завершён', 'В архиве')
            ORDER BY o.order_date DESC, o.order_id DESC
        """
        return self.fetch_all(query)

    def get_research_result(
        self, order_service_id: int
    ) -> dict[str, Any] | None:
        """Получить результат исследования по order_service_id."""
        query = """
            SELECT research_id, result_value, conclusion, result_date, employee_id
            FROM research_results
            WHERE order_service_id = %s
        """
        return self.fetch_one(query, (order_service_id,))

    def save_research_result(
        self,
        order_service_id: int,
        employee_id: int,
        result_value: str,
        conclusion: str,
        result_date: Any,
    ) -> int:
        """Сохранить или обновить результат исследования. Возвращает research_id."""
        existing = self.fetch_one(
            "SELECT research_id FROM research_results WHERE order_service_id = %s",
            (order_service_id,),
        )

        if existing:
            research_id = int(existing["research_id"])
            self.update(
                """
                UPDATE research_results
                SET result_value = %s,
                    conclusion   = %s,
                    result_date  = %s,
                    employee_id  = %s
                WHERE order_service_id = %s
                """,
                (result_value, conclusion, result_date, employee_id, order_service_id),
            )
            return research_id

        research_id = self.insert(
            """
            INSERT INTO research_results
                (order_service_id, result_value, conclusion, result_date, employee_id)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (order_service_id, result_value, conclusion, result_date, employee_id),
        )
        return int(research_id)

    # ------------------------------------------------------------------
    # Исследования по заказу (для отчётов)
    # ------------------------------------------------------------------

    def get_report_research(self, order_id: int) -> list[dict[str, Any]]:
        """Исследования по конкретному заказу (для таблицы в отчёте)."""
        query = """
            SELECT s.service_name, rr.result_value, rr.conclusion
            FROM order_services os
            JOIN services s ON s.service_id = os.service_id
            LEFT JOIN research_results rr
                ON rr.order_service_id = os.order_service_id
            WHERE os.order_id = %s
            ORDER BY s.service_name
        """
        return self.fetch_all(query, (order_id,))

    # ------------------------------------------------------------------
    # Отчёты
    # ------------------------------------------------------------------

    def get_recent_reports(self, limit: int = 10) -> list[dict[str, Any]]:
        """Получить последние отчёты."""
        query = """
            SELECT r.report_id, o.vessel_code, r.report_date, e.full_name AS employee_name
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            JOIN employees e ON e.employee_id = r.employee_id
            ORDER BY r.report_date DESC
            LIMIT %s
        """
        return self.fetch_all(query, (limit,))

    def get_report(self, report_id: int) -> dict[str, Any] | None:
        """Получить данные отчёта по ID."""
        query = """
            SELECT r.report_id, r.order_id, r.employee_id, r.report_date, r.file_path,
                   o.vessel_code,
                   CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                        ELSE i.full_name END AS client_name,
                   e.full_name AS employee_name
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            JOIN clients c ON c.client_id = o.client_id
            LEFT JOIN legal_entities le
                ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
            LEFT JOIN individuals i
                ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
            JOIN employees e ON e.employee_id = r.employee_id
            WHERE r.report_id = %s
        """
        return self.fetch_one(query, (report_id,))

    def get_report_by_order(self, order_id: int) -> dict[str, Any] | None:
        """Получить последний отчёт по заказу (для проверки дубликата)."""
        query = """
            SELECT r.report_id, r.order_id, r.employee_id, r.report_date, r.file_path,
                   o.vessel_code,
                   CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                        ELSE i.full_name END AS client_name,
                   e.full_name AS employee_name
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            JOIN clients c ON c.client_id = o.client_id
            LEFT JOIN legal_entities le
                ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
            LEFT JOIN individuals i
                ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
            JOIN employees e ON e.employee_id = r.employee_id
            WHERE r.order_id = %s
            ORDER BY r.report_date DESC
            LIMIT 1
        """
        return self.fetch_one(query, (order_id,))

    def create_report(
        self, order_id: int, employee_id: int, file_path: str | None
    ) -> int:
        """Создать запись отчёта в БД. Возвращает report_id."""
        return self.insert(
            "INSERT INTO reports (order_id, employee_id, file_path) VALUES (%s, %s, %s)",
            (order_id, employee_id, file_path),
        )

    def get_next_report_number(self) -> int:
        """Получить следующий номер отчёта."""
        row = self.fetch_one("SELECT MAX(report_id) AS max_id FROM reports")
        max_id = int(row["max_id"]) if row and row["max_id"] is not None else 0
        return max_id + 1

    def get_report_by_path(self, file_path: str) -> dict[str, Any] | None:
        """Найти отчёт по пути к файлу."""
        query = """
            SELECT r.report_id, r.order_id, r.report_date, r.file_path,
                   o.vessel_code, e.full_name AS employee_name
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            JOIN employees e ON e.employee_id = r.employee_id
            WHERE r.file_path = %s
        """
        return self.fetch_one(query, (file_path,))

    def delete_report(self, report_id: int) -> None:
        """Удалить отчёт из базы данных."""
        self.update("DELETE FROM reports WHERE report_id = %s", (report_id,))

    def update_report_path(self, report_id: int, file_path: str) -> None:
        """Обновить путь к файлу отчёта."""
        self.update(
            "UPDATE reports SET file_path = %s WHERE report_id = %s",
            (file_path, report_id),
        )


__all__ = ["ReportRepository"]
