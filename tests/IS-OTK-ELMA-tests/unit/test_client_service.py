"""Unit-тесты для ClientService."""

from __future__ import annotations

import hashlib
import pytest

from services.client_service import ClientService


class TestClientServiceRead:
    """Тесты чтения клиентов."""

    def test_get_all_clients(self, client_service, client_repo_mock):
        """Получение всех активных клиентов."""
        client_repo_mock.get_all_clients.return_value = [
            {"client_id": 1, "name": "Клиент 1", "type": "ЮЛ"}
        ]

        result = client_service.get_all_clients()

        assert len(result) == 1
        client_repo_mock.get_all_clients.assert_called_once()

    def test_get_clients_by_type_legal(self, client_service, client_repo_mock):
        """Клиенты типа ЮЛ."""
        client_repo_mock.get_clients_by_type.return_value = [
            {"client_id": 1, "name": "ООО Компания"}
        ]

        result = client_service.get_clients_by_type("ЮЛ")

        assert len(result) == 1
        client_repo_mock.get_clients_by_type.assert_called_once_with("ЮЛ")

    def test_get_clients_by_type_individual(self, client_service, client_repo_mock):
        """Клиенты типа ФЛ."""
        client_repo_mock.get_clients_by_type.return_value = [
            {"client_id": 2, "name": "Иванов И.И."}
        ]

        result = client_service.get_clients_by_type("ФЛ")

        assert len(result) == 1
        client_repo_mock.get_clients_by_type.assert_called_once_with("ФЛ")

    def test_get_clients_by_type_invalid_raises(self, client_service):
        """Некорректный тип — ValueError."""
        with pytest.raises(ValueError, match="Некорректный тип клиента"):
            client_service.get_clients_by_type("invalid")
        with pytest.raises(ValueError, match="Некорректный тип клиента"):
            client_service.get_clients_by_type("")

    def test_get_client_by_id_success(self, client_service, client_repo_mock):
        """Получение клиента по ID."""
        client_repo_mock.get_client_by_id.return_value = {
            "client_id": 1, "name": "Тест"
        }

        result = client_service.get_client_by_id(1)

        assert result["client_id"] == 1

    def test_get_client_by_id_invalid_raises(self, client_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID клиента"):
            client_service.get_client_by_id(0)

    def test_get_client_details(self, client_service, client_repo_mock):
        """Детальная информация о клиенте."""
        client_repo_mock.get_client_details.return_value = {
            "client_id": 1, "name": "Тест", "orders_count": 5
        }

        result = client_service.get_client_details(1)

        assert result["orders_count"] == 5

    def test_get_client_stats(self, client_service, client_repo_mock):
        """Статистика клиента."""
        client_repo_mock.get_client_stats.return_value = {
            "total_orders": 10, "total_amount": 50000
        }

        result = client_service.get_client_stats(1)

        assert result["total_orders"] == 10

    def test_get_clients_stats(self, client_service, client_repo_mock):
        """Общая статистика."""
        client_repo_mock.get_clients_stats.return_value = {
            "total": 50, "active": 45, "legal_entities": 30, "individuals": 15
        }

        result = client_service.get_clients_stats()

        assert result["total"] == 50

    def test_get_clients_orders_count(self, client_service, client_repo_mock):
        """Количество заказов по клиентам."""
        client_repo_mock.get_clients_orders_count.return_value = {1: 5, 2: 3}

        result = client_service.get_clients_orders_count()

        assert result == {1: 5, 2: 3}


class TestClientServiceClientData:
    """Тесты заказов, отчётов, результатов клиента."""

    def test_get_client_orders(self, client_service, client_repo_mock):
        """Заказы клиента."""
        client_repo_mock.get_client_orders.return_value = [
            {"order_id": 1, "vessel_code": "LS-001"}
        ]

        result = client_service.get_client_orders(1, limit=5)

        assert len(result) == 1
        client_repo_mock.get_client_orders.assert_called_once_with(1, 5)

    def test_get_client_reports(self, client_service, client_repo_mock):
        """Отчёты клиента."""
        client_repo_mock.get_client_reports.return_value = [
            {"report_id": 1, "order_id": 1}
        ]

        result = client_service.get_client_reports(1)

        assert len(result) == 1

    def test_get_client_results(self, client_service, client_repo_mock):
        """Результаты исследований клиента."""
        client_repo_mock.get_client_results.return_value = [
            {"result_id": 1, "order_id": 1}
        ]

        result = client_service.get_client_results(1)

        assert len(result) == 1


class TestClientServiceAuth:
    """Тесты авторизации клиента."""

    def test_authenticate_client_success(self, client_service, client_repo_mock):
        """Успешная авторизация."""
        password_hash = hashlib.sha256("clientpass".encode()).hexdigest()
        client_repo_mock.get_client_by_login.return_value = {
            "client_id": 1, "name": "Тест", "type": "ЮЛ"
        }

        result = client_service.authenticate_client("test@company.ru", "clientpass")

        assert result is not None
        assert result["client_id"] == 1
        call_args = client_repo_mock.get_client_by_login.call_args
        assert call_args[0][0] == "test@company.ru"
        assert call_args[0][1] == password_hash

    def test_authenticate_client_wrong_password_returns_none(self, client_service, client_repo_mock):
        """Неверный пароль — None."""
        client_repo_mock.get_client_by_login.return_value = None

        result = client_service.authenticate_client("test@company.ru", "wrong")

        assert result is None

    def test_authenticate_client_empty_login_raises(self, client_service):
        """Пустой логин — ValueError."""
        with pytest.raises(ValueError, match="Логин обязателен"):
            client_service.authenticate_client("", "password")

    def test_authenticate_client_empty_password_raises(self, client_service):
        """Пустой пароль — ValueError."""
        with pytest.raises(ValueError, match="Пароль обязателен"):
            client_service.authenticate_client("login", "")

    def test_authenticate_client_trims_login(self, client_service, client_repo_mock):
        """Логин обрезается."""
        client_repo_mock.get_client_by_login.return_value = None

        client_service.authenticate_client("  test@company.ru  ", "password")

        call_args = client_repo_mock.get_client_by_login.call_args
        assert call_args[0][0] == "test@company.ru"

    def test_client_login_exists(self, client_service, client_repo_mock):
        """Проверка существования логина."""
        client_repo_mock.client_login_exists.return_value = True

        result = client_service.client_login_exists("test@company.ru")

        assert result is True
        client_repo_mock.client_login_exists.assert_called_once_with("test@company.ru", None)

    def test_client_login_exists_with_exclude(self, client_service, client_repo_mock):
        """Проверка с исключением ID."""
        client_repo_mock.client_login_exists.return_value = False

        client_service.client_login_exists("test@company.ru", exclude_id=1)

        client_repo_mock.client_login_exists.assert_called_once_with("test@company.ru", 1)

    def test_client_login_exists_empty_raises(self, client_service):
        """Пустой логин — ValueError."""
        with pytest.raises(ValueError, match="Логин обязателен"):
            client_service.client_login_exists("")


class TestClientServiceCreate:
    """Тесты создания клиента."""

    def test_create_client_success(self, client_service, client_repo_mock, sample_client_data):
        """Успешное создание клиента ЮЛ."""
        client_repo_mock.client_login_exists.return_value = False
        client_repo_mock.create_client.return_value = 42

        client_id = client_service.create_client(
            client_type=sample_client_data["client_type"],
            name=sample_client_data["name"],
            phone=sample_client_data["phone"],
            email=sample_client_data["email"],
            password=sample_client_data["password"],
            address=sample_client_data["address"],
            inn=sample_client_data["inn"],
            kpp=sample_client_data["kpp"],
        )

        assert client_id == 42
        client_repo_mock.create_client.assert_called_once()
        call_args = client_repo_mock.create_client.call_args
        assert call_args.kwargs["client_type"] == "ЮЛ"
        assert call_args.kwargs["name"] == sample_client_data["name"]

    def test_create_client_invalid_type_raises(self, client_service):
        """Некорректный тип — ValueError."""
        with pytest.raises(ValueError, match="Некорректный тип клиента"):
            client_service.create_client("invalid", "Name", password="pass123")

    def test_create_client_empty_name_raises(self, client_service):
        """Пустое название — ValueError."""
        with pytest.raises(ValueError, match="Название"):
            client_service.create_client("ЮЛ", "", password="pass123")

    def test_create_client_missing_email_phone_raises(self, client_service):
        """Нет email и телефона — ValueError."""
        with pytest.raises(ValueError, match="E-mail или телефон"):
            client_service.create_client("ЮЛ", "Name", password="pass123")

    def test_create_client_empty_password_raises(self, client_service):
        """Пустой пароль — ValueError."""
        with pytest.raises(ValueError, match="Пароль обязателен"):
            client_service.create_client("ЮЛ", "Name", email="test@test.ru", password="")

    def test_create_client_no_duplicate_check_in_service(self, client_service, client_repo_mock):
        """create_client не проверяет дубликаты email/телефона (проверка в репозитории/БД)."""
        client_repo_mock.client_login_exists.return_value = True
        client_repo_mock.create_client.return_value = 1

        # Сервис НЕ вызывает client_login_exists при создании
        client_id = client_service.create_client("ЮЛ", "Name", email="exists@test.ru", password="pass123")
        assert client_id == 1
        # create_client не должен вызывать client_login_exists
        client_repo_mock.client_login_exists.assert_not_called()

    def test_create_client_password_hashed(self, client_service, client_repo_mock):
        """Пароль хешируется в сервисе."""
        client_repo_mock.client_login_exists.return_value = False
        client_repo_mock.create_client.return_value = 1

        client_service.create_client("ЮЛ", "Name", email="test@test.ru", password="plain_password")

        call_args = client_repo_mock.create_client.call_args
        # Пароль хешируется внутри сервиса перед передачей в репозиторий
        assert "password_hash" in call_args.kwargs
        import hashlib
        expected_hash = hashlib.sha256("plain_password".encode()).hexdigest()
        assert call_args.kwargs["password_hash"] == expected_hash


class TestClientServiceUpdate:
    """Тесты обновления клиента."""

    def test_update_client(self, client_service, client_repo_mock):
        """Обновление клиента - требует client_type и name."""
        client_repo_mock.update_client.return_value = True

        client_service.update_client(1, client_type="ЮЛ", name="Новое название", phone="+7-999-000-00-00")

        client_repo_mock.update_client.assert_called_once_with(
            client_id=1, client_type="ЮЛ", name="Новое название", phone="+7-999-000-00-00", email="", password_hash=None
        )

    def test_update_client_with_password(self, client_service, client_repo_mock):
        """Обновление клиента с сменой пароля."""
        client_repo_mock.update_client.return_value = True

        client_service.update_client(1, client_type="ЮЛ", name="Name", password="newpass123")

        call_args = client_repo_mock.update_client.call_args
        import hashlib
        expected_hash = hashlib.sha256("newpass123".encode()).hexdigest()
        assert call_args.kwargs["password_hash"] == expected_hash

    def test_update_client_invalid_id_raises(self, client_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID клиента"):
            client_service.update_client(0, client_type="ЮЛ", name="Name")

    def test_update_client_invalid_type_raises(self, client_service):
        """Некорректный тип — ValueError."""
        with pytest.raises(ValueError, match="Некорректный тип клиента"):
            client_service.update_client(1, client_type="invalid", name="Name")

    def test_update_client_empty_name_raises(self, client_service):
        """Пустое название — ValueError."""
        with pytest.raises(ValueError, match="Название / ФИО обязательно"):
            client_service.update_client(1, client_type="ЮЛ", name="")


class TestClientServiceLogAction:
    """Тесты логирования."""

    def test_log_action(self, client_service, caplog):
        """Логирование действия."""
        with caplog.at_level("INFO"):
            client_service.log_action("create_client", 42, 1, "via admin panel")

        assert "Пользователь 1 выполнил 'create_client' над объектом 42 (via admin panel)" in caplog.text