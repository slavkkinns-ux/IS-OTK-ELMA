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