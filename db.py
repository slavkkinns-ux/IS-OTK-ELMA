import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG

class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self):
        if self._connection and self._connection.open:
            return
        
        try:
            self._connection = pymysql.connect(
                host=DB_CONFIG['host'],
                user=DB_CONFIG['user'],
                password=DB_CONFIG['password'],
                database=DB_CONFIG['database'],
                cursorclass=DictCursor,
                charset='utf8mb4'
            )
        except pymysql.Error as e:
            print(f"Ошибка подключения к БД: {e}")
            raise

    def get_connection(self):
        if not self._connection or not self._connection.open:
            self.connect()
        return self._connection

    def execute_query(self, query, params=None):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"Ошибка выполнения запроса: {e}")
            connection.rollback()
            raise

    def execute_insert(self, query, params=None):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                connection.commit()
                return cursor.lastrowid
        except pymysql.Error as e:
            print(f"Ошибка вставки: {e}")
            connection.rollback()
            raise

    def get_all_clients(self):
        connection = self.get_connection()
        try:
            with connection.cursor() as cursor:
                query = """
                    SELECT 
                        c.client_id,
                        c.client_type,
                        c.phone,
                        c.email,
                        CASE 
                            WHEN c.client_type = 'FL' THEN i.full_name 
                            WHEN c.client_type = 'UL' THEN l.company_name 
                        END as name,
                        CASE 
                            WHEN c.client_type = 'FL' THEN CONCAT(i.passport_series, ' ', i.passport_number)
                            WHEN c.client_type = 'UL' THEN l.inn 
                        END as details,
                        CASE 
                            WHEN c.client_type = 'FL' THEN i.full_name
                            WHEN c.client_type = 'UL' THEN l.contact_person 
                        END as contact_person
                    FROM clients c
                    LEFT JOIN individuals i ON c.client_id = i.client_id
                    LEFT JOIN legal_entities l ON c.client_id = l.client_id
                    ORDER BY c.client_id DESC
                """
                cursor.execute(query)
                return cursor.fetchall()
        except pymysql.Error as e:
            print(f"Ошибка получения клиентов: {e}")
            return []

    def close(self):
        if self._connection and self._connection.open:
            self._connection.close()

    def get_home_stats(self):
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

    def get_clients_stats(self):
        query = """
            SELECT
                (SELECT COUNT(*) FROM clients) AS total_clients,
                (SELECT COUNT(DISTINCT client_id) FROM orders WHERE status <> 'Завершён') AS active_clients,
                (SELECT COUNT(DISTINCT client_id) FROM orders) AS clients_with_orders
        """
        try:
            result = self.execute_query(query)
            return result[0] if result else None
        except pymysql.Error:
            return None

    def get_recent_orders(self, limit=5):
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

    def get_all_orders(self):
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

    def get_research_queue(self):
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