"""Модуль управления соединением с БД (синглтон)."""
import pymysql
from pymysql import Error
import logging

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Синглтон, хранит одно активное соединение."""
    _instance = None
    _connection = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def get_connection(self):
        """Возвращает активное соединение, открывая его при необходимости."""
        if self._connection is None or not self._connection.open:
            try:
                from config import DB_CONFIG
                self._connection = pymysql.connect(
                    **DB_CONFIG,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False,
                    connect_timeout=5,
                )
                logger.info("Соединение с БД установлено")
            except Error as e:
                logger.error(f"Ошибка подключения к БД: {e}")
                self._connection = None
                raise
        return self._connection

    def close(self):
        """Закрывает соединение."""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None
            logger.info("Соединение с БД закрыто")

    def is_connected(self):
        """Проверяет, активно ли соединение."""
        return self._connection is not None and self._connection.open


connection_manager = ConnectionManager()


def get_connection():
    """Публичная функция — используется во всех репозиториях."""
    return connection_manager.get_connection()


def close_connection():
    """Публичная функция — вызывается при закрытии приложения."""
    connection_manager.close()


def is_db_available():
    """Проверяет доступность БД без создания постоянного соединения."""
    try:
        from config import DB_CONFIG
        conn = pymysql.connect(**DB_CONFIG, connect_timeout=3)
        conn.close()
        return True
    except Exception:
        return False