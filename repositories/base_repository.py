"""Базовый репозиторий: общее подключение и выполнение SQL-запросов."""

import pymysql
from pymysql.cursors import DictCursor
from config import DB_CONFIG


class BaseRepository:
    """Общая логика подключения к MySQL и выполнения запросов.

    Соединение хранится на уровне класса, чтобы все репозитории
    работали через одно подключение, как прежний синглтон Database.
    """

    _connection = None

    def connect(self):
        """Открывает соединение с базой, если оно ещё не открыто."""
        if self._connection and self._connection.open:
            return

        try:
            BaseRepository._connection = pymysql.connect(
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
        """Возвращает активное соединение, открывая его при необходимости."""
        if not self._connection or not self._connection.open:
            self.connect()
        return self._connection

    def execute_query(self, query, params=None):
        """Выполняет запрос и возвращает все строки результата.

        Args:
            query: SQL-запрос с плейсхолдерами %s.
            params: Параметры запроса.

        Returns:
            Список словарей с результатом выборки.
        """
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
        """Выполняет INSERT и возвращает идентификатор новой строки.

        Args:
            query: SQL-запрос с плейсхолдерами %s.
            params: Параметры запроса.

        Returns:
            Идентификатор вставленной строки.
        """
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
        """Закрывает общее соединение с базой данных."""
        if self._connection and self._connection.open:
            self._connection.close()
