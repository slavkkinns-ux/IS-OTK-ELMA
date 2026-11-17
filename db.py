"""Фасад доступа к базе данных.

Импортирует и инициализирует специализированные репозитории.
Доменные выборки выполняются через client_repo, order_repo и report_repo.
Низкоуровневые connect, execute_query и execute_insert остаются на фасаде
и на base_repo.
"""

from repositories.base_repository import BaseRepository
from repositories.client_repository import ClientRepository
from repositories.order_repository import OrderRepository
from repositories.report_repository import ReportRepository


class Database:
    """Синглтон-фасад над репозиториями базы данных."""

    _instance = None

    def __new__(cls):
        """Создаёт единственный экземпляр и привязывает к нему репозитории."""
        if cls._instance is None:
            instance = super().__new__(cls)
            instance.base_repo = BaseRepository()
            instance.client_repo = ClientRepository()
            instance.order_repo = OrderRepository()
            instance.report_repo = ReportRepository()
            cls._instance = instance
        return cls._instance

    def connect(self):
        """Открывает соединение с базой данных."""
        self.base_repo.connect()

    def get_connection(self):
        """Возвращает активное соединение, при необходимости открывая его."""
        return self.base_repo.get_connection()

    def execute_query(self, query, params=None):
        """Выполняет SQL-запрос и возвращает все строки.

        Args:
            query: SQL-запрос с плейсхолдерами %s.
            params: Параметры запроса.
        """
        return self.base_repo.execute_query(query, params)

    def execute_insert(self, query, params=None):
        """Выполняет INSERT и возвращает идентификатор новой строки.

        Args:
            query: SQL-запрос с плейсхолдерами %s.
            params: Параметры запроса.
        """
        return self.base_repo.execute_insert(query, params)

    def close(self):
        """Закрывает соединение с базой данных."""
        self.base_repo.close()


_db = Database()
base_repo = _db.base_repo
client_repo = _db.client_repo
order_repo = _db.order_repo
report_repo = _db.report_repo