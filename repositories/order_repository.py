from repositories.base_repository import BaseRepository


class OrderRepository(BaseRepository):

    def get_all_orders(self) -> list:
        """Получить все заказы."""
        query = """
        SELECT 
            o.order_id,
            o.vessel_code,
            o.order_date,
            o.status,
            COALESCE(le.company_name, i.full_name,
                    CONCAT('Клиент #', c.client_id)) AS client_name,
            e.full_name AS employee_name
        FROM orders o
        JOIN clients c ON o.client_id = c.client_id
        LEFT JOIN legal_entities le ON le.client_id = c.client_id
        LEFT JOIN individuals    i  ON i.client_id  = c.client_id
        JOIN employees e ON o.employee_id = e.employee_id
        ORDER BY o.order_date DESC
        """
        return self.execute_query(query)

    def get_order(self, order_id: int) -> dict:
        """Получить заказ по ID."""
        query = """
        SELECT 
            o.order_id,
            o.vessel_code,
            o.order_date,
            o.status,
            c.client_id,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.company_name
                WHEN c.client_type = 'ФЛ' THEN i.full_name
            END AS client_name,
            e.full_name AS employee_name
        FROM orders o
        JOIN clients c ON o.client_id = c.client_id
        LEFT JOIN legal_entities le ON c.client_id = le.client_id AND c.client_type = 'ЮЛ'
        LEFT JOIN individuals i ON c.client_id = i.client_id AND c.client_type = 'ФЛ'
        JOIN employees e ON o.employee_id = e.employee_id
        WHERE o.order_id = %s
        """
        results = self.execute_query(query, (order_id,))
        return results[0] if results else None

    def get_order_services(self, order_id: int) -> list:
        """Получить услуги заказа."""
        query = """
        SELECT 
            os.order_service_id,
            os.service_id,
            s.service_name,
            os.price_at_order AS price
        FROM order_services os
        JOIN services s ON os.service_id = s.service_id
        WHERE os.order_id = %s
        ORDER BY os.order_service_id
        """
        return self.execute_query(query, (order_id,))

    def get_active_services(self) -> list:
        """Получить активные услуги (справочник)."""
        query = """
        SELECT service_id, service_name, price
        FROM services
        WHERE is_active = 1
        ORDER BY service_name
        """
        return self.execute_query(query)

    def create_order(self, payload: dict) -> int:
        """Создать заказ с услугами."""
        queries = [
            (
                """INSERT INTO orders (vessel_code, client_id, employee_id, status)
                   VALUES (%s, %s, %s, %s)""",
                (payload["vessel_code"], payload["client_id"],
                 payload["employee_id"], payload["status"])
            )
        ]
        
        conn = self.execute_query.__self__.get_connection()
        try:
            with conn.cursor() as cursor:
                # Вставляем заказ
                cursor.execute(queries[0][0], queries[0][1])
                order_id = cursor.lastrowid
                
                # Вставляем услуги
                for service in payload["services"]:
                    cursor.execute(
                        """INSERT INTO order_services (order_id, service_id, price_at_order)
                           VALUES (%s, %s, %s)""",
                        (order_id, service["service_id"], service["price"])
                    )
                conn.commit()
                return order_id
        except Exception as e:
            conn.rollback()
            raise

    def update_order(self, order_id: int, payload: dict):
        """Обновить заказ."""
        conn = self.execute_query.__self__.get_connection()
        try:
            with conn.cursor() as cursor:
                # Обновляем шапку
                cursor.execute(
                    """UPDATE orders
                       SET vessel_code = %s, client_id = %s, status = %s
                       WHERE order_id = %s""",
                    (payload["vessel_code"], payload["client_id"],
                     payload["status"], order_id)
                )
                
                # Удаляем старые услуги
                cursor.execute("DELETE FROM order_services WHERE order_id = %s", (order_id,))
                
                # Вставляем новые
                for service in payload["services"]:
                    cursor.execute(
                        """INSERT INTO order_services (order_id, service_id, price_at_order)
                           VALUES (%s, %s, %s)""",
                        (order_id, service["service_id"], service["price"])
                    )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise

    def search_orders(self, query: str) -> list:
        """Поиск заказов."""
        like = f"%{query}%"
        sql = """
        SELECT 
            o.order_id,
            o.vessel_code,
            o.order_date,
            o.status,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.company_name
                WHEN c.client_type = 'ФЛ' THEN i.full_name
            END AS client_name,
            e.full_name AS employee_name
        FROM orders o
        JOIN clients c ON o.client_id = c.client_id
        LEFT JOIN legal_entities le ON c.client_id = le.client_id AND c.client_type = 'ЮЛ'
        LEFT JOIN individuals i ON c.client_id = i.client_id AND c.client_type = 'ФЛ'
        JOIN employees e ON o.employee_id = e.employee_id
        WHERE o.vessel_code LIKE %s
           OR le.company_name LIKE %s
           OR i.full_name LIKE %s
           OR o.status LIKE %s
        ORDER BY o.order_date DESC
        """
        return self.execute_query(sql, (like, like, like, like))

    def get_recent_orders(self, limit: int = 5) -> list:
        query = """
        SELECT 
            o.order_id,
            o.vessel_code,
            o.order_date,
            o.status,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.company_name
                WHEN c.client_type = 'ФЛ' THEN i.full_name
            END AS client_name
        FROM orders o
        JOIN clients c ON o.client_id = c.client_id
        LEFT JOIN legal_entities le ON c.client_id = le.client_id AND c.client_type = 'ЮЛ'
        LEFT JOIN individuals i ON c.client_id = i.client_id AND c.client_type = 'ФЛ'
        ORDER BY o.order_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))

    def get_home_stats(self) -> dict:
        """Статистика для главной страницы."""
        query = """
        SELECT 
            COUNT(*) AS total_orders,
            SUM(CASE WHEN status IN ('Новый', 'В работе') THEN 1 ELSE 0 END) AS active_orders,
            (SELECT COUNT(*) FROM clients WHERE is_active = 1) AS total_clients,
            SUM(CASE WHEN status = 'Ожидает проверки' THEN 1 ELSE 0 END) AS pending_checks
        FROM orders
        """
        results = self.execute_query(query)
        return results[0] if results else {}

    def get_orders_stats(self) -> dict:
        """Статистика заказов."""
        query = """
        SELECT 
            COUNT(*) AS total,
            SUM(CASE WHEN status IN ('Новый', 'В работе') THEN 1 ELSE 0 END) AS in_progress,
            SUM(CASE WHEN status = 'Ожидает проверки' THEN 1 ELSE 0 END) AS pending,
            SUM(CASE WHEN status = 'Завершён' THEN 1 ELSE 0 END) AS completed
        FROM orders
        """
        results = self.execute_query(query)
        return results[0] if results else {}