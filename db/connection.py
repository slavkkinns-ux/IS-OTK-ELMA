"""Модуль управления соединением с БД (синглтон)."""
import pymysql
from pymysql import Error
from config import DB_CONFIG
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
                self._connection = pymysql.connect(
                    **DB_CONFIG,
                    cursorclass=pymysql.cursors.DictCursor,
                    autocommit=False,
                )
                logger.info("Соединение с БД установлено")
            except Error as e:
                logger.error(f"Ошибка подключения к БД: {e}")
                raise
        return self._connection

    def close(self):
        """Закрывает соединение."""
        if self._connection and self._connection.open:
            self._connection.close()
            self._connection = None
            logger.info("Соединение с БД закрыто")


connection_manager = ConnectionManager()


def get_connection():
    """Публичная функция — используется во всех репозиториях."""
    return connection_manager.get_connection()


def close_connection():
    """Публичная функция — вызывается при закрытии приложения."""
    connection_manager.close()