"""Конфигурация pytest и общие фикстуры для тестов ИС ОТК ЭЛМА."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Добавляем корень проекта в sys.path для импорта модулей приложения
PROJECT_ROOT = Path(r"C:\Users\Вячеслав\.local\share\opencode\worktree\a589cd\shiny-wizard")
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def mock_db():
    """Мок соединения с БД (pymysql connection)."""
    conn = MagicMock()
    cursor = MagicMock()
    conn.cursor.return_value.__enter__.return_value = cursor
    conn.cursor.return_value.__exit__.return_value = None
    conn.commit = MagicMock()
    conn.rollback = MagicMock()
    conn.ping = MagicMock(return_value=True)
    return conn


@pytest.fixture
def mock_cursor():
    """Мок курсора БД."""
    return MagicMock()


@pytest.fixture
def employee_repo_mock():
    """Мок EmployeeRepository."""
    from unittest.mock import MagicMock
    repo = MagicMock()
    repo.get_all_employees.return_value = []
    repo.get_employee.return_value = None
    repo.get_employee_by_login.return_value = None
    repo.create_employee.return_value = 1
    repo.update_employee.return_value = True
    repo.reset_password.return_value = True
    repo.get_employee_stats.return_value = {
        "total": 0, "active": 0, "managers": 0,
        "lab_technicians": 0, "controllers": 0, "admins": 0,
    }
    repo.check_login_exists.return_value = False
    return repo


@pytest.fixture
def client_repo_mock():
    """Мок ClientRepository."""
    from unittest.mock import MagicMock
    repo = MagicMock()
    repo.get_all_clients.return_value = []
    repo.get_clients_by_type.return_value = []
    repo.get_client_by_id.return_value = None
    repo.get_client_details.return_value = None
    repo.get_client_stats.return_value = {}
    repo.get_clients_stats.return_value = {"total": 0, "active": 0, "legal_entities": 0, "individuals": 0}
    repo.get_clients_orders_count.return_value = {}
    repo.get_client_orders.return_value = []
    repo.get_client_reports.return_value = []
    repo.get_client_results.return_value = []
    repo.get_client_by_login.return_value = None
    repo.client_login_exists.return_value = False
    repo.create_client.return_value = 1
    repo.update_client.return_value = True
    repo.reset_client_password.return_value = True
    return repo


@pytest.fixture
def order_repo_mock():
    """Мок OrderRepository."""
    from unittest.mock import MagicMock
    repo = MagicMock()
    repo.get_all_orders.return_value = []
    repo.get_order.return_value = None
    repo.get_order_services.return_value = []
    repo.get_active_services.return_value = []
    repo.search_orders.return_value = []
    repo.get_orders_stats.return_value = {"total": 0, "active": 0, "completed": 0, "archived": 0}
    repo.get_home_stats.return_value = {"total_orders": 0, "active_orders": 0, "total_clients": 0, "total_employees": 0}
    repo.get_recent_orders.return_value = []
    repo.get_next_vessel_code.return_value = "LS-001"
    repo.vessel_code_exists.return_value = False
    repo.create_order.return_value = 1
    repo.update_order.return_value = True
    repo.update_order_status.return_value = True
    repo.archive_order.return_value = True
    repo.delete_order.return_value = True
    return repo


@pytest.fixture
def service_repo_mock():
    """Мок ServiceRepository."""
    from unittest.mock import MagicMock
    repo = MagicMock()
    repo.get_all_services.return_value = []
    repo.get_service_by_id.return_value = None
    repo.get_active_services.return_value = []
    repo.create_service.return_value = 1
    repo.update_service.return_value = True
    repo.delete_service.return_value = True
    repo.service_name_exists.return_value = False
    repo.is_service_used.return_value = False
    return repo


@pytest.fixture
def report_repo_mock():
    """Мок ReportRepository."""
    from unittest.mock import MagicMock
    repo = MagicMock()
    repo.get_all_reports.return_value = []
    repo.get_report_by_id.return_value = None
    repo.get_reports_by_order.return_value = []
    repo.create_report.return_value = 1
    repo.update_report.return_value = True
    repo.delete_report.return_value = True
    return repo


@pytest.fixture
def employee_service(employee_repo_mock):
    """Экземпляр EmployeeService с замоканным репозиторием."""
    from services.employee_service import EmployeeService
    return EmployeeService(employee_repo_mock)


@pytest.fixture
def client_service(client_repo_mock):
    """Экземпляр ClientService с замоканным репозиторием."""
    from services.client_service import ClientService
    return ClientService(client_repo_mock)


@pytest.fixture
def order_service(order_repo_mock, client_repo_mock, service_repo_mock):
    """Экземпляр OrderService с замоканными репозиториями."""
    from services.order_service import OrderService
    return OrderService(order_repo_mock, client_repo_mock, service_repo_mock)


@pytest.fixture
def service_service(service_repo_mock):
    """Экземпляр ServiceService с замоканным репозиторием."""
    from services.service_service import ServiceService
    return ServiceService(service_repo_mock)


@pytest.fixture
def report_service(report_repo_mock, order_repo_mock):
    """Экземпляр ReportService с замоканными репозиториями."""
    from services.report_service import ReportService
    return ReportService(report_repo_mock, order_repo_mock)


@pytest.fixture
def connection_service():
    """Экземпляр ConnectionService (использует реальную БД через DatabaseConnection)."""
    from services.connection_service import ConnectionService
    return ConnectionService()


@pytest.fixture
def sample_employee_data():
    """Тестовые данные сотрудника."""
    return {
        "full_name": "Иванов Иван Иванович",
        "login": "ivanov",
        "password": "password123",
        "role": "controller",
        "is_active": True,
        "email": "ivanov@example.com",
        "phone": "+7-900-123-45-67",
    }


@pytest.fixture
def sample_client_data():
    """Тестовые данные клиента."""
    return {
        "client_type": "ЮЛ",
        "name": "ООО «ТестКомпания»",
        "phone": "+7-495-123-45-67",
        "email": "test@company.ru",
        "password": "clientpass123",
        "address": "г. Москва, ул. Тестовая, д. 1",
        "inn": "7701234567",
        "kpp": "770101001",
    }


@pytest.fixture
def sample_order_data():
    """Тестовые данные заказа."""
    return {
        "vessel_code": "LS-001",
        "client_id": 1,
        "employee_id": 1,
        "service_ids": [1, 2],
        "total_price": 15000.00,
    }


# Маркеры для категорий тестов
def pytest_configure(config):
    config.addinivalue_line("markers", "unit: Unit-тесты (быстрые, без БД)")
    config.addinivalue_line("markers", "integration: Интеграционные тесты (с реальной БД)")
    config.addinivalue_line("markers", "slow: Медленные тесты")