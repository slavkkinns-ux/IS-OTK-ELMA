"""Репозиторий отчётов и очереди исследований."""

import pymysql

from repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):
    """Операции чтения по исследованиям и отчётам."""

    def get_research_queue(self):
        """Возвращает очередь исследований по услугам заказов."""
        query = """
            SELECT 
                os.order_service_id,
                o.order_id,
                o.vessel_code,
                s.service_name,
                CASE 
                    WHEN c.client_type = 'FL' THEN i.full_name 
                    WHEN c.client_type = 'UL' THEN l.company_name 
                END as client_name,
                rr.result_value,
                rr.conclusion,
                DATE_FORMAT(rr.result_date, '%%d.%%m.%%Y') as result_date,
                rr.research_id
            FROM order_services os
            JOIN orders o ON os.order_id = o.order_id
            JOIN services s ON os.service_id = s.service_id
            LEFT JOIN clients c ON o.client_id = c.client_id
            LEFT JOIN individuals i ON c.client_id = i.client_id
            LEFT JOIN legal_entities l ON c.client_id = l.client_id
            LEFT JOIN research_results rr ON os.order_service_id = rr.order_service_id
            ORDER BY o.order_date DESC
        """
        try:
            return self.execute_query(query)
        except pymysql.Error:
            return []

    def get_report_research(self, order_id):
        """Возвращает результаты исследований для отчёта по заказу.

        Args:
            order_id: Идентификатор заказа.
        """
        query = """
            SELECT 
                s.service_name,
                rr.result_value,
                rr.conclusion
            FROM order_services os
            JOIN services s ON os.service_id = s.service_id
            LEFT JOIN research_results rr ON os.order_service_id = rr.order_service_id
            WHERE os.order_id = %s
        """
        try:
            return self.execute_query(query, (order_id,))
        except pymysql.Error:
            return []

    def get_recent_reports(self, limit=10):
        """Возвращает последние сформированные отчёты.

        Args:
            limit: Максимальное число строк.
        """
        query = f"""
            SELECT 
                r.report_id,
                o.vessel_code,
                DATE_FORMAT(r.report_date, '%%d.%%m.%%Y') as report_date,
                e.full_name as employee_name
            FROM reports r
            JOIN orders o ON r.order_id = o.order_id
            JOIN employees e ON r.employee_id = e.employee_id
            ORDER BY r.report_date DESC
            LIMIT {int(limit)}
        """
        try:
            return self.execute_query(query)
        except pymysql.Error:
            return []

    def save_research_result(self, order_service_id, result_value, conclusion, result_date, employee_id):
        """Сохраняет результат исследования.

        Args:
            order_service_id: Идентификатор услуги в заказе.
            result_value: Значение результата.
            conclusion: Заключение.
            result_date: Дата результата.
            employee_id: Идентификатор сотрудника.

        Returns:
            Идентификатор созданной записи или None при ошибке.
        """
        query = """
            INSERT INTO research_results (order_service_id, result_value, conclusion, result_date, employee_id)
            VALUES (%s, %s, %s, %s, %s)
        """
        try:
            return self.execute_insert(query, (order_service_id, result_value, conclusion, result_date, employee_id))
        except pymysql.Error as e:
            print(f"Ошибка сохранения результата исследования: {e}")
            return None

    def create_report(self, order_id, employee_id, file_path=None):
        """Создаёт отчёт по заказу.

        Args:
            order_id: Идентификатор заказа.
            employee_id: Идентификатор сотрудника.
            file_path: Путь к файлу отчёта (опционально).

        Returns:
            Идентификатор созданного отчёта или None при ошибке.
        """
        query = """
            INSERT INTO reports (order_id, employee_id, file_path)
            VALUES (%s, %s, %s)
        """
        try:
            return self.execute_insert(query, (order_id, employee_id, file_path))
        except pymysql.Error as e:
            print(f"Ошибка создания отчёта: {e}")
            return None
