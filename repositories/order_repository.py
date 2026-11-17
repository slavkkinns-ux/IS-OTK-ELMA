"""Репозиторий заказов: статистика и списки заказов."""

import pymysql

from repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):
    """Операции чтения, связанные с заказами."""

    def get_home_stats(self):
        """Возвращает сводные показатели для главной страницы."""
        query = """
            SELECT
                (SELECT COUNT(*) FROM orders) AS total_orders,
                (SELECT COUNT(*) FROM orders WHERE status <> 'Завершён') AS active_orders,
                (SELECT COUNT(*) FROM clients) AS total_clients,
                (SELECT COUNT(*) FROM orders WHERE status = 'Ожидает контроля') AS pending_checks
        """
        try:
            result = self.execute_query(query)
            return result[0] if result else None
        except pymysql.Error:
            return None

    def get_orders_stats(self):
        """Возвращает счётчики заказов по статусам."""
        query = """
            SELECT
                (SELECT COUNT(*) FROM orders) AS total,
                (SELECT COUNT(*) FROM orders WHERE status = 'В работе') AS in_progress,
                (SELECT COUNT(*) FROM orders WHERE status = 'Ожидает контроля') AS pending,
                (SELECT COUNT(*) FROM orders WHERE status = 'Завершён') AS completed
        """
        try:
            result = self.execute_query(query)
            return result[0] if result else None
        except pymysql.Error:
            return None

    def get_recent_orders(self, limit=5):
        """Возвращает последние заказы.

        Args:
            limit: Максимальное число строк.
        """
        query = f"""
            SELECT 
                o.vessel_code,
                CASE 
                    WHEN c.client_type = 'FL' THEN i.full_name 
                    WHEN c.client_type = 'UL' THEN l.company_name 
                END as client_name,
                DATE_FORMAT(o.order_date, '%d.%m.%Y') as order_date,
                o.status
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.client_id
            LEFT JOIN individuals i ON c.client_id = i.client_id
            LEFT JOIN legal_entities l ON c.client_id = l.client_id
            ORDER BY o.order_date DESC
            LIMIT {int(limit)}
        """
        try:
            return self.execute_query(query)
        except pymysql.Error as e:
            print(f"Ошибка в get_recent_orders: {e}")
            return []

    def get_all_orders(self):
        """Возвращает полный список заказов с клиентом и сотрудником."""
        query = """
            SELECT 
                o.order_id,
                o.vessel_code,
                CASE 
                    WHEN c.client_type = 'FL' THEN i.full_name 
                    WHEN c.client_type = 'UL' THEN l.company_name 
                END as client_name,
                DATE_FORMAT(o.order_date, '%d.%m.%Y') as order_date,
                e.full_name as employee_name,
                o.status,
                NULL as completion_date
            FROM orders o
            LEFT JOIN clients c ON o.client_id = c.client_id
            LEFT JOIN individuals i ON c.client_id = i.client_id
            LEFT JOIN legal_entities l ON c.client_id = l.client_id
            LEFT JOIN employees e ON o.employee_id = e.employee_id
            ORDER BY o.order_date DESC
        """
        try:
            return self.execute_query(query)
        except pymysql.Error:
            return []
