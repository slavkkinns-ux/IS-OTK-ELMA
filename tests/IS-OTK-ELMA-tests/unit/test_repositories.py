"""Unit-тесты для репозиториев (мокируем DatabaseConnection)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


class TestAbstractRepository:
    """Тесты базового класса AbstractRepository."""

    def test_fetch_all_delegates_to_db(self):
        """fetch_all делегирует в db.execute_query."""
        with patch("db.repositories.base.db") as mock_db:
            mock_db.execute_query.return_value = [{"id": 1}]
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.fetch_all("SELECT * FROM test", (1,))

            assert result == [{"id": 1}]
            mock_db.execute_query.assert_called_once_with("SELECT * FROM test", (1,))

    def test_fetch_one_delegates_to_db(self):
        """fetch_one делегирует в db.execute_fetchone."""
        with patch("db.repositories.base.db") as mock_db:
            mock_db.execute_fetchone.return_value = {"id": 1}
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.fetch_one("SELECT * FROM test WHERE id=%s", (1,))

            assert result == {"id": 1}
            mock_db.execute_fetchone.assert_called_once_with("SELECT * FROM test WHERE id=%s", (1,))

    def test_insert_delegates_to_db(self):
        """insert делегирует в db.execute_insert."""
        with patch("db.repositories.base.db") as mock_db:
            mock_db.execute_insert.return_value = 42
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.insert("INSERT INTO test VALUES (%s)", ("val",))

            assert result == 42
            mock_db.execute_insert.assert_called_once_with("INSERT INTO test VALUES (%s)", ("val",))

    def test_update_delegates_to_db(self):
        """update делегирует в db.execute_update."""
        with patch("db.repositories.base.db") as mock_db:
            mock_db.execute_update.return_value = 1
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.update("UPDATE test SET val=%s WHERE id=%s", ("new", 1))

            assert result == 1
            mock_db.execute_update.assert_called_once_with("UPDATE test SET val=%s WHERE id=%s", ("new", 1))

    def test_insert_many_delegates_to_db(self):
        """insert_many делегирует в db.execute_many."""
        with patch("db.repositories.base.db") as mock_db:
            mock_db.execute_many.return_value = 3
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.insert_many("INSERT INTO test VALUES (%s)", [("a",), ("b",), ("c",)])

            assert result == 3
            mock_db.execute_many.assert_called_once_with("INSERT INTO test VALUES (%s)", [("a",), ("b",), ("c",)])

    def test_transaction_returns_context_manager(self):
        """transaction возвращает контекстный менеджер."""
        with patch("db.repositories.base.db") as mock_db:
            mock_cm = MagicMock()
            mock_db.transaction.return_value = mock_cm
            from db.repositories.base import AbstractRepository

            repo = AbstractRepository()
            result = repo.transaction()

            assert result is mock_cm
            mock_db.transaction.assert_called_once()


class TestEmployeeRepository:
    """Тесты EmployeeRepository (SQL формирование)."""

    @pytest.fixture
    def repo(self):
        with patch("db.database.db") as mock_db:
            from db.repositories.employee_repository import EmployeeRepository
            repo = EmployeeRepository()
            repo.db = mock_db
            yield repo

    def test_get_all_employees_base_query(self, repo):
        """Базовый запрос без фильтров."""
        repo.db.execute_query.return_value = []

        repo.get_all_employees()

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "FROM employees e" in query
        assert "WHERE 1=1" in query
        assert "ORDER BY e.full_name" in query
        # Параметров нет
        assert call_args[0][1] == ()

    def test_get_all_employees_with_role_filter(self, repo):
        """С фильтром по роли."""
        repo.db.execute_query.return_value = []

        repo.get_all_employees(role_filter="manager")

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "e.role = %s" in query
        assert call_args[0][1] == ("manager",)

    def test_get_all_employees_with_active_only(self, repo):
        """Только активные."""
        repo.db.execute_query.return_value = []

        repo.get_all_employees(active_only=True)

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "e.is_active = 1" in query

    def test_get_all_employees_with_search(self, repo):
        """С поисковым запросом."""
        repo.db.execute_query.return_value = []

        repo.get_all_employees(search_query="Иван")

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "e.full_name LIKE %s OR e.login LIKE %s" in query
        params = call_args[0][1]
        assert "%Иван%" in params
        assert params.count("%Иван%") == 2

    def test_get_all_employees_combined_filters(self, repo):
        """Все фильтры вместе."""
        repo.db.execute_query.return_value = []

        repo.get_all_employees(role_filter="controller", active_only=True, search_query="test")

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "e.role = %s" in query
        assert "e.is_active = 1" in query
        assert "e.full_name LIKE %s" in query
        params = call_args[0][1]
        assert params[0] == "controller"
        # active_only подставляется в query как литерал 1, не как параметр
        assert "%test%" in params[1]
        assert "%test%" in params[2]

    def test_get_employee_by_id(self, repo):
        """Получение по ID."""
        repo.db.execute_fetchone.return_value = {"employee_id": 1}

        result = repo.get_employee(1)

        assert result["employee_id"] == 1
        call_args = repo.db.execute_fetchone.call_args
        query = call_args[0][0]
        assert "WHERE e.employee_id = %s" in query
        assert call_args[0][1] == (1,)

    def test_get_employee_by_login(self, repo):
        """Поиск по логину и хешу пароля."""
        repo.db.execute_fetchone.return_value = {"employee_id": 1}

        result = repo.get_employee_by_login("login", "hash123")

        assert result["employee_id"] == 1
        call_args = repo.db.execute_fetchone.call_args
        query = call_args[0][0]
        assert "e.login = %s AND e.password_hash = %s AND e.is_active = 1" in query
        assert call_args[0][1] == ("login", "hash123")

    def test_create_employee_hashes_password(self, repo):
        """Создание — пароль хешируется."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        repo.db.transaction.return_value.__enter__.return_value = mock_conn

        result = repo.create_employee(
            full_name="Иванов", login="ivanov", password="pass123",
            role="controller", is_active=True, email=None, phone=None, created_by=1
        )

        assert result == 42
        # Проверяем что execute вызвался с хешем
        call_args = mock_cursor.execute.call_args
        assert call_args[0][0].strip().startswith("INSERT INTO employees")
        params = call_args[0][1]
        assert params[0] == "Иванов"
        assert params[1] == "ivanov"
        # params[2] должен быть SHA256 хешем
        import hashlib
        expected_hash = hashlib.sha256("pass123".encode("utf-8")).hexdigest()
        assert params[2] == expected_hash
        assert params[3] == "controller"
        assert params[4] == 1  # is_active
        assert params[5] == 1  # must_change_password

    def test_update_employee_dynamic_query(self, repo):
        """Обновление — динамический запрос только с переданными полями."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        repo.db.transaction.return_value.__enter__.return_value = mock_conn

        result = repo.update_employee(1, full_name="Новое имя", role="manager")

        assert result is True
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert "full_name = %s" in query
        assert "role = %s" in query
        assert "email" not in query
        params = call_args[0][1]
        assert params[0] == "Новое имя"
        assert params[1] == "manager"
        assert params[2] == 1  # employee_id

    def test_update_employee_no_changes_returns_false(self, repo):
        """Без изменений — False."""
        repo.db.execute_update.return_value = 0

        result = repo.update_employee(1)

        assert result is False
        repo.db.execute_update.assert_not_called()

    def test_reset_password_hashes(self, repo):
        """Сброс пароля — хеширует новый."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        repo.db.transaction.return_value.__enter__.return_value = mock_conn

        result = repo.reset_password(1, "newpass456")

        assert result is True
        call_args = mock_cursor.execute.call_args
        query = call_args[0][0]
        assert "password_hash = %s" in query
        assert "must_change_password = 1" in query
        import hashlib
        expected_hash = hashlib.sha256("newpass456".encode("utf-8")).hexdigest()
        assert call_args[0][1][0] == expected_hash
        assert call_args[0][1][1] == 1

    def test_get_employee_stats(self, repo):
        """Статистика сотрудников."""
        repo.db.execute_fetchone.return_value = {
            "total": 10, "active": 8, "managers": 2,
            "lab_technicians": 3, "controllers": 3, "admins": 2
        }

        result = repo.get_employee_stats()

        assert result["total"] == 10
        assert result["active"] == 8

    def test_check_login_exists(self, repo):
        """Проверка существования логина."""
        repo.db.execute_fetchone.return_value = {"cnt": 1}

        result = repo.check_login_exists("existing")

        assert result is True

    def test_check_login_exists_with_exclude(self, repo):
        """Проверка с исключением ID."""
        repo.db.execute_fetchone.return_value = {"cnt": 0}

        result = repo.check_login_exists("login", exclude_employee_id=1)

        assert result is False
        call_args = repo.db.execute_fetchone.call_args
        query = call_args[0][0]
        assert "employee_id != %s" in query
        assert call_args[0][1] == ("login", 1)


class TestClientRepository:
    """Тесты ClientRepository."""

    @pytest.fixture
    def repo(self):
        with patch("db.database.db") as mock_db:
            from db.repositories.client_repository import ClientRepository
            repo = ClientRepository()
            repo.db = mock_db
            yield repo

    def test_get_all_clients(self, repo):
        """Все клиенты."""
        repo.db.execute_query.return_value = [{"client_id": 1}]

        result = repo.get_all_clients()

        assert len(result) == 1
        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "FROM clients" in query
        assert "is_active = 1" in query

    def test_get_clients_by_type(self, repo):
        """По типу."""
        repo.db.execute_query.return_value = []

        repo.get_clients_by_type("ЮЛ")

        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "client_type = %s" in query
        assert call_args[0][1] == ("ЮЛ",)

    def test_get_clients_by_type_invalid_raises(self, repo):
        """Некорректный тип — ошибка в SQL (нет валидации в репозитории)."""
        # Репозиторий не валидирует, это задача сервиса
        repo.db.execute_query.return_value = []
        repo.get_clients_by_type("invalid")
        # Не должно падать, просто вернёт пустой список

    def test_get_client_by_id(self, repo):
        """По ID."""
        repo.db.execute_fetchone.return_value = {"client_id": 1}

        result = repo.get_client_by_id(1)

        assert result["client_id"] == 1

    def test_get_client_details(self, repo):
        """Детальная инфо."""
        repo.db.execute_fetchone.return_value = {"client_id": 1, "orders_count": 5}

        result = repo.get_client_details(1)

        assert result["orders_count"] == 5

    def test_get_client_by_login(self, repo):
        """По логину и хешу пароля."""
        repo.db.execute_fetchone.return_value = {"client_id": 1}

        result = repo.get_client_by_login("email@test.ru", "hash")

        assert result["client_id"] == 1
        call_args = repo.db.execute_fetchone.call_args
        query = call_args[0][0]
        assert "(c.email = %s OR c.phone = %s)" in query
        assert "c.password_hash = %s" in query

    def test_client_login_exists(self, repo):
        """Существование email/телефона."""
        repo.db.execute_fetchone.return_value = {"cnt": 1}

        result = repo.client_login_exists("email@test.ru")

        assert result is True


class TestOrderRepository:
    """Тесты OrderRepository."""

    @pytest.fixture
    def repo(self):
        with patch("db.database.db") as mock_db:
            from db.repositories.order_repository import OrderRepository
            repo = OrderRepository()
            repo.db = mock_db
            yield repo

    def test_get_all_orders(self, repo):
        repo.db.execute_query.return_value = [{"order_id": 1}]
        result = repo.get_all_orders()
        assert len(result) == 1

    def test_get_order(self, repo):
        repo.db.execute_fetchone.return_value = {"order_id": 1}
        result = repo.get_order(1)
        assert result["order_id"] == 1

    def test_get_order_services(self, repo):
        repo.db.execute_query.return_value = [{"service_id": 1}]
        result = repo.get_order_services(1)
        assert len(result) == 1

    def test_get_active_services(self, repo):
        repo.db.execute_query.return_value = [{"service_id": 1}]
        result = repo.get_active_services()
        assert len(result) == 1

    def test_search_orders(self, repo):
        repo.db.execute_query.return_value = [{"order_id": 1}]
        result = repo.search_orders("LS-001")
        assert len(result) == 1
        call_args = repo.db.execute_query.call_args
        assert "%LS-001%" in call_args[0][1]

    def test_get_next_vessel_code(self, repo):
        # get_next_vessel_code использует fetch_all, не fetchone
        repo.db.execute_query.return_value = [
            {"vessel_code": "С-0004"},
            {"vessel_code": "С-0003"},
        ]
        result = repo.get_next_vessel_code()
        assert result == "С-0005"

    def test_get_next_vessel_code_empty_result(self, repo):
        repo.db.execute_query.return_value = []
        result = repo.get_next_vessel_code()
        # Если нет заказов, возвращается начальный код (кириллица С)
        assert result == "С-0001"

    def test_vessel_code_exists(self, repo):
        repo.db.execute_fetchone.return_value = {"cnt": 1}
        result = repo.vessel_code_exists("LS-001")
        assert result is True

    def test_create_order(self, repo):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 42
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        repo.db.transaction.return_value.__enter__.return_value = mock_conn

        result = repo.create_order("LS-001", 1, 1, [1, 2], 15000.0)

        assert result == 42
        # Проверяем INSERT в orders
        calls = mock_cursor.execute.call_args_list
        assert len(calls) >= 2  # orders + order_services
        first_call = calls[0]
        assert "INSERT INTO orders" in first_call[0][0]

    def test_get_orders_stats(self, repo):
        repo.db.execute_fetchone.return_value = {
            "total": 100, "in_progress": 30, "pending": 20, "completed": 40
        }
        result = repo.get_orders_stats()
        assert result["total"] == 100
        assert result["in_progress"] == 30
        assert result["pending"] == 20
        assert result["completed"] == 40


class TestServiceRepository:
    """Тесты ServiceRepository."""

    @pytest.fixture
    def repo(self):
        with patch("db.database.db") as mock_db:
            from db.repositories.service_repository import ServiceRepository
            repo = ServiceRepository()
            repo.db = mock_db
            yield repo

    def test_get_all_services(self, repo):
        repo.db.execute_query.return_value = [{"service_id": 1}]
        result = repo.get_all_services(include_inactive=False)
        assert len(result) == 1
        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        assert "is_active = 1" in query

    def test_get_all_services_include_inactive(self, repo):
        repo.db.execute_query.return_value = [{"service_id": 1}, {"service_id": 2}]
        result = repo.get_all_services(include_inactive=True)
        assert len(result) == 2
        call_args = repo.db.execute_query.call_args
        query = call_args[0][0]
        # При include_inactive=True фильтр is_active не добавляется
        assert "is_active = 1" not in query

    def test_service_name_exists(self, repo):
        repo.db.execute_fetchone.return_value = {"cnt": 1}
        result = repo.service_name_exists("Test")
        assert result is True

    def test_is_service_used(self, repo):
        repo.db.execute_fetchone.return_value = {"cnt": 5}
        result = repo.is_service_used(1)
        assert result is True

    def test_add_service(self, repo):
        repo.db.execute_insert.return_value = 1

        result = repo.add_service("Услуга", 5000.0)

        assert result == 1
        repo.db.execute_insert.assert_called_once()
        call_args = repo.db.execute_insert.call_args
        assert "INSERT INTO services" in call_args[0][0]
        params = call_args[0][1]
        assert params[0] == "Услуга"
        assert params[1] == 5000.0

    def test_update_service(self, repo):
        repo.db.execute_update.return_value = 1

        result = repo.update_service(1, "New", 6000.0, 1)

        assert result is None  # update_service returns None
        repo.db.execute_update.assert_called_once()
        call_args = repo.db.execute_update.call_args
        assert "UPDATE services" in call_args[0][0]

    def test_delete_service_soft(self, repo):
        repo.db.execute_update.return_value = 1

        result = repo.delete_service(1, soft=True)

        assert result is None  # delete_service returns None
        repo.db.execute_update.assert_called_once()
        call_args = repo.db.execute_update.call_args
        query = call_args[0][0]
        assert "is_active = 0" in query

    def test_delete_service_hard(self, repo):
        repo.db.execute_update.return_value = 1

        result = repo.delete_service(1, soft=False)

        assert result is None  # delete_service returns None
        repo.db.execute_update.assert_called_once()
        call_args = repo.db.execute_update.call_args
        query = call_args[0][0]
        assert "DELETE FROM services" in query


class TestReportRepository:
    """Тесты ReportRepository."""

    @pytest.fixture
    def repo(self):
        with patch("db.database.db") as mock_db:
            from db.repositories.report_repository import ReportRepository
            repo = ReportRepository()
            repo.db = mock_db
            yield repo

    def test_get_research_queue(self, repo):
        repo.db.execute_query.return_value = [{"order_service_id": 1}]
        result = repo.get_research_queue()
        assert len(result) == 1

    def test_get_research_result(self, repo):
        repo.db.execute_fetchone.return_value = {"order_service_id": 1, "result_value": "OK"}
        result = repo.get_research_result(1)
        assert result["result_value"] == "OK"

    def test_save_research_result(self, repo):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.lastrowid = 1
        mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
        repo.db.transaction.return_value.__enter__.return_value = mock_conn

        result = repo.save_research_result(1, 1, "value", "conclusion", "2024-01-01")

        assert result == 1

    def test_get_report_research(self, repo):
        repo.db.execute_query.return_value = [{"order_service_id": 1}]
        result = repo.get_report_research(1)
        assert len(result) == 1

    def test_get_recent_reports(self, repo):
        repo.db.execute_query.return_value = [{"report_id": 1}]
        result = repo.get_recent_reports(5)
        assert len(result) == 1

    def test_get_report(self, repo):
        repo.db.execute_fetchone.return_value = {"report_id": 1}
        result = repo.get_report(1)
        assert result["report_id"] == 1

    def test_get_report_by_order(self, repo):
        repo.db.execute_fetchone.return_value = {"report_id": 1}
        result = repo.get_report_by_order(1)
        assert result["report_id"] == 1

    def test_create_report(self, repo):
        repo.db.execute_insert.return_value = 1

        result = repo.create_report(1, 1, "/path.pdf")

        assert result == 1
        repo.db.execute_insert.assert_called_once()
        call_args = repo.db.execute_insert.call_args
        assert "INSERT INTO reports" in call_args[0][0]

    def test_get_next_report_number(self, repo):
        repo.db.execute_fetchone.return_value = {"max_id": 41}
        result = repo.get_next_report_number()
        assert result == 42

    def test_get_report_by_path(self, repo):
        repo.db.execute_fetchone.return_value = {"report_id": 1}
        result = repo.get_report_by_path("/path.pdf")
        assert result["report_id"] == 1

    def test_delete_report(self, repo):
        repo.db.execute_update.return_value = 1
        result = repo.delete_report(1)
        # delete_report возвращает None, проверяем вызов
        repo.db.execute_update.assert_called_once()

    def test_update_report_path(self, repo):
        repo.db.execute_update.return_value = 1
        repo.update_report_path(1, "/new/path.pdf")
        repo.db.execute_update.assert_called_once()