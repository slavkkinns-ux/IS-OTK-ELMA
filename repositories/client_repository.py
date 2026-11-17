"""Репозиторий клиентов: выборки по клиентам и их данным."""

import pymysql

from repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository):
    """Операции чтения, связанные с клиентами."""

    def get_all_clients(self):
        """Возвращает список всех клиентов с именем и реквизитами."""
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

    def get_clients_stats(self):
        """Возвращает сводную статистику по клиентам."""
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

    def get_client_by_login(self, login, password_hash):
        """Ищет активного клиента по логину и хешу пароля.

        Args:
            login: Логин клиента.
            password_hash: Хеш пароля.

        Returns:
            Словарь с данными клиента или None.
        """
        query = """
            SELECT 
                c.client_id, 
                c.login, 
                c.email, 
                c.client_type, 
                c.phone,
                COALESCE(l.company_name, i.full_name) as full_name,
                COALESCE(l.contact_person, i.full_name) as contact_person
            FROM clients c
            LEFT JOIN legal_entities l ON c.client_id = l.client_id
            LEFT JOIN individuals i ON c.client_id = i.client_id
            WHERE c.login = %s AND c.password_hash = %s AND c.is_active = 1
        """
        try:
            result = self.execute_query(query, (login, password_hash))
            return result[0] if result else None
        except Exception as e:
            print(f"get_client_by_login error: {e}")
            return None

    def get_client_stats(self, client_id):
        """Возвращает счётчики заказов конкретного клиента.

        Args:
            client_id: Идентификатор клиента.
        """
        query = """
            SELECT COUNT(*) as total_orders,
                   SUM(CASE WHEN status IN ('Новый', 'В работе') THEN 1 ELSE 0 END) as active_orders,
                   SUM(CASE WHEN status = 'Завершён' THEN 1 ELSE 0 END) as completed_orders
            FROM orders WHERE client_id = %s AND is_archived = 0
        """
        try:
            result = self.execute_query(query, (client_id,))
            return result[0] if result else None
        except Exception:
            return None

    def get_client_orders(self, client_id, limit=None):
        """Возвращает заказы клиента.

        Args:
            client_id: Идентификатор клиента.
            limit: Необязательное ограничение числа строк.
        """
        query = """
            SELECT o.order_id, o.vessel_code, DATE_FORMAT(o.order_date, '%%d.%%m.%%Y') as order_date,
                   o.status, COUNT(os.order_service_id) as services_count,
                   SUM(os.price_at_order) as total_price,
                   GROUP_CONCAT(s.service_name SEPARATOR ', ') as services_list
            FROM orders o
            LEFT JOIN order_services os ON o.order_id = os.order_id
            LEFT JOIN services s ON os.service_id = s.service_id
            WHERE o.client_id = %s AND o.is_archived = 0
            GROUP BY o.order_id, o.vessel_code, o.order_date, o.status
            ORDER BY o.order_date DESC
        """
        if limit:
            query += f" LIMIT {int(limit)}"
        try:
            return self.execute_query(query, (client_id,))
        except Exception:
            return []

    def get_client_results(self, client_id):
        """Возвращает результаты исследований клиента.

        Args:
            client_id: Идентификатор клиента.
        """
        query = """
            SELECT o.vessel_code, s.service_name, DATE_FORMAT(rr.result_date, '%%d.%%m.%%Y') as result_date,
                   rr.result_value, rr.conclusion, e.full_name as employee_name
            FROM orders o JOIN order_services os ON o.order_id = os.order_id
            JOIN services s ON os.service_id = s.service_id
            LEFT JOIN research_results rr ON os.order_service_id = rr.order_service_id
            LEFT JOIN employees e ON rr.employee_id = e.employee_id
            WHERE o.client_id = %s AND o.is_archived = 0 ORDER BY rr.result_date DESC
        """
        try:
            return self.execute_query(query, (client_id,))
        except Exception:
            return []

    def get_client_reports(self, client_id):
        """Возвращает отчёты клиента.

        Args:
            client_id: Идентификатор клиента.
        """
        query = """
            SELECT r.report_id, o.vessel_code, DATE_FORMAT(r.report_date, '%%d.%%m.%%Y') as report_date
            FROM reports r JOIN orders o ON r.order_id = o.order_id
            WHERE o.client_id = %s ORDER BY r.report_date DESC
        """
        try:
            return self.execute_query(query, (client_id,))
        except Exception:
            return []

    def get_client_info(self, client_id):
        """Получает информацию о клиенте для профиля.

        Args:
            client_id: Идентификатор клиента.

        Returns:
            Словарь с контактными данными или None.
        """
        query = """
            SELECT 
                c.email, 
                c.phone, 
                COALESCE(l.company_name, i.full_name) as name,
                COALESCE(l.contact_person, i.full_name) as contact_person
            FROM clients c
            LEFT JOIN legal_entities l ON c.client_id = l.client_id
            LEFT JOIN individuals i ON c.client_id = i.client_id
            WHERE c.client_id = %s
        """
        try:
            result = self.execute_query(query, (client_id,))
            return result[0] if result else None
        except Exception as e:
            print(f"get_client_info error: {e}")
            return None

    def create_client(self, client_data):
        """Создаёт нового клиента с данными ФЛ или ЮЛ.

        Args:
            client_data: Словарь с данными клиента:
                - client_type: 'FL' или 'UL'
                - phone: Телефон
                - email: Email
                - login: Логин (опционально)
                - password_hash: Хеш пароля (опционально)
                - is_active: Активен ли клиент
                - Для ФЛ: full_name, birth_date, passport_series, passport_number
                - Для ЮЛ: company_name, address, inn, kpp, checking_account, bik, director_name, contact_person

        Returns:
            Идентификатор созданного клиента или None при ошибке.
        """
        client_type = client_data['client_type']
        connection = self.get_connection()

        try:
            with connection.cursor() as cursor:
                # Создаём клиента
                cursor.execute(
                    """INSERT INTO clients (client_type, phone, email, login, password_hash, is_active)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (
                        client_type,
                        client_data.get('phone', ''),
                        client_data.get('email', ''),
                        client_data.get('login'),
                        client_data.get('password_hash'),
                        client_data.get('is_active', 1)
                    )
                )
                client_id = cursor.lastrowid

                if client_type == 'FL':
                    cursor.execute(
                        """INSERT INTO individuals (client_id, full_name, birth_date, passport_series, passport_number)
                           VALUES (%s, %s, %s, %s, %s)""",
                        (
                            client_id,
                            client_data.get('full_name', ''),
                            client_data.get('birth_date') or None,
                            client_data.get('passport_series', ''),
                            client_data.get('passport_number', '')
                        )
                    )
                else:  # UL
                    cursor.execute(
                        """INSERT INTO legal_entities (client_id, company_name, address, inn, kpp,
                                                       checking_account, bik, director_name, contact_person)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                        (
                            client_id,
                            client_data.get('company_name', ''),
                            client_data.get('address', ''),
                            client_data.get('inn', ''),
                            client_data.get('kpp', ''),
                            client_data.get('checking_account', ''),
                            client_data.get('bik', ''),
                            client_data.get('director_name', ''),
                            client_data.get('contact_person', '')
                        )
                    )

                connection.commit()
                return client_id
        except pymysql.Error as e:
            connection.rollback()
            print(f"Ошибка создания клиента: {e}")
            return None

    def search_clients(self, search_text):
        """Поиск клиентов по имени, компании или телефону.

        Args:
            search_text: Текст для поиска.

        Returns:
            Список найденных клиентов.
        """
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
            WHERE i.full_name LIKE %s
               OR l.company_name LIKE %s
               OR c.phone LIKE %s
            ORDER BY c.client_id DESC
        """
        like = f"%{search_text}%"
        try:
            return self.execute_query(query, (like, like, like))
        except pymysql.Error as e:
            print(f"Ошибка поиска клиентов: {e}")
            return []
