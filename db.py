import pymysql
from pymysql.cursors import DictCursor

class Database:
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def connect(self, host='localhost', user='root', password='', database='elma'):
        if self._connection and self._connection.open:
            return
        
        try:
            self._connection = pymysql.connect(
                host=host,
                user=user,
                password=password,
                database=database,
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

    def close(self):
        if self._connection and self._connection.open:
            self._connection.close()