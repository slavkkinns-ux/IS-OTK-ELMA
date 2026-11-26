"""Unit-тесты для OrderService."""

from __future__ import annotations

import pytest

from services.order_service import OrderService


class TestOrderServiceRead:
    """Тесты чтения заказов."""

    def test_get_all_orders(self, order_service, order_repo_mock):
        """Получение всех заказов."""
        order_repo_mock.get_all_orders.return_value = [
            {"order_id": 1, "vessel_code": "LS-001", "status": "active"}
        ]

        result = order_service.get_all_orders()

        assert len(result) == 1
        order_repo_mock.get_all_orders.assert_called_once()

    def test_get_order_success(self, order_service, order_repo_mock):
        """Успешное получение заказа по ID."""
        order_repo_mock.get_order.return_value = {
            "order_id": 1, "vessel_code": "LS-001", "client_id": 1
        }

        result = order_service.get_order(1)

        assert result["order_id"] == 1
        order_repo_mock.get_order.assert_called_once_with(1)

    def test_get_order_invalid_id_raises(self, order_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID заказа"):
            order_service.get_order(0)
        with pytest.raises(ValueError, match="Некорректный ID заказа"):
            order_service.get_order(-5)

    def test_get_order_services(self, order_service, order_repo_mock):
        """Получение услуг заказа."""
        order_repo_mock.get_order_services.return_value = [
            {"service_id": 1, "name": "Услуга 1", "price": 5000}
        ]

        result = order_service.get_order_services(1)

        assert len(result) == 1
        order_repo_mock.get_order_services.assert_called_once_with(1)

    def test_get_active_services(self, order_service, order_repo_mock):
        """Получение активных услуг."""
        order_repo_mock.get_active_services.return_value = [
            {"service_id": 1, "name": "Активная услуга"}
        ]

        result = order_service.get_active_services()

        assert len(result) == 1
        order_repo_mock.get_active_services.assert_called_once()

    def test_search_orders_success(self, order_service, order_repo_mock):
        """Успешный поиск заказов."""
        order_repo_mock.search_orders.return_value = [
            {"order_id": 1, "vessel_code": "LS-001"}
        ]

        result = order_service.search_orders("LS-001")

        assert len(result) == 1
        order_repo_mock.search_orders.assert_called_once_with("LS-001")

    def test_search_orders_empty_query_raises(self, order_service):
        """Пустой запрос — ValueError."""
        with pytest.raises(ValueError, match="Поисковой запрос обязателен"):
            order_service.search_orders("")
        with pytest.raises(ValueError, match="Поисковой запрос обязателен"):
            order_service.search_orders("   ")

    def test_search_orders_trims_query(self, order_service, order_repo_mock):
        """Запрос обрезается по пробелам."""
        order_repo_mock.search_orders.return_value = []

        order_service.search_orders("  LS-001  ")

        order_repo_mock.search_orders.assert_called_once_with("LS-001")

    def test_get_orders_stats(self, order_service, order_repo_mock):
        """Статистика заказов."""
        order_repo_mock.get_orders_stats.return_value = {
            "total": 100, "active": 20, "completed": 70, "archived": 10
        }

        result = order_service.get_orders_stats()

        assert result["total"] == 100
        assert result["active"] == 20

    def test_get_home_stats(self, order_service, order_repo_mock):
        """Статистика для главной страницы."""
        order_repo_mock.get_home_stats.return_value = {
            "total_orders": 50, "active_orders": 10
        }

        result = order_service.get_home_stats()

        assert result["total_orders"] == 50

    def test_get_recent_orders(self, order_service, order_repo_mock):
        """Последние заказы."""
        order_repo_mock.get_recent_orders.return_value = [
            {"order_id": 5, "vessel_code": "LS-005"}
        ]

        result = order_service.get_recent_orders(5)

        assert len(result) == 1
        order_repo_mock.get_recent_orders.assert_called_once_with(5)

    def test_get_recent_orders_invalid_limit_raises(self, order_service):
        """Некорректный лимит — ValueError."""
        with pytest.raises(ValueError, match="Некорректный лимит"):
            order_service.get_recent_orders(0)
        with pytest.raises(ValueError, match="Некорректный лимит"):
            order_service.get_recent_orders(-1)


class TestOrderServiceVesselCode:
    """Тесты кодов сосудов."""

    def test_get_next_vessel_code(self, order_service, order_repo_mock):
        """Генерация следующего кода."""
        order_repo_mock.get_next_vessel_code.return_value = "LS-042"

        result = order_service.get_next_vessel_code()

        assert result == "LS-042"

    def test_vessel_code_exists_true(self, order_service, order_repo_mock):
        """Код существует — True."""
        order_repo_mock.vessel_code_exists.return_value = True

        result = order_service.vessel_code_exists("LS-001")

        assert result is True

    def test_vessel_code_exists_false(self, order_service, order_repo_mock):
        """Код не существует — False."""
        order_repo_mock.vessel_code_exists.return_value = False

        result = order_service.vessel_code_exists("LS-999")

        assert result is False

    def test_vessel_code_exists_empty_raises(self, order_service):
        """Пустой код — ValueError."""
        with pytest.raises(ValueError, match="Код сосуда обязателен"):
            order_service.vessel_code_exists("")
        with pytest.raises(ValueError, match="Код сосуда обязателен"):
            order_service.vessel_code_exists("   ")

    def test_vessel_code_exists_trims(self, order_service, order_repo_mock):
        """Код обрезается."""
        order_repo_mock.vessel_code_exists.return_value = False

        order_service.vessel_code_exists("  LS-001  ")

        order_repo_mock.vessel_code_exists.assert_called_once_with(
            "LS-001", exclude_archived=True, exclude_order_id=None
        )


class TestOrderServiceClients:
    """Тесты клиентов для заказа."""

    def test_get_clients_by_type(self, order_service, client_repo_mock):
        """Получение клиентов по типу."""
        client_repo_mock.get_clients_by_type.return_value = [
            {"client_id": 1, "name": "Клиент 1"}
        ]

        result = order_service.get_clients_by_type("ЮЛ")

        assert len(result) == 1
        client_repo_mock.get_clients_by_type.assert_called_once_with("ЮЛ")


class TestOrderServiceCreate:
    """Тесты создания заказа."""

    def test_create_order_success(self, order_service, order_repo_mock):
        """Успешное создание заказа."""
        order_repo_mock.vessel_code_exists.return_value = False
        order_repo_mock.create_order.return_value = 42

        order_id = order_service.create_order(
            vessel_code="LS-001",
            client_id=1,
            employee_id=1,
            service_ids=[1, 2],
            total_price=15000.00,
        )

        assert order_id == 42
        order_repo_mock.create_order.assert_called_once_with(
            vessel_code="LS-001",
            client_id=1,
            employee_id=1,
            service_ids=[1, 2],
            total_price=15000.00,
        )

    def test_create_order_empty_vessel_code_raises(self, order_service):
        """Пустой код сосуда — ValueError."""
        with pytest.raises(ValueError, match="Код сосуда обязателен"):
            order_service.create_order("", 1, 1, [1], 1000)

    def test_create_order_vessel_code_trimmed(self, order_service, order_repo_mock):
        """Код сосуда обрезается."""
        order_repo_mock.vessel_code_exists.return_value = False
        order_repo_mock.create_order.return_value = 1

        order_service.create_order("  LS-001  ", 1, 1, [1], 1000)

        order_repo_mock.vessel_code_exists.assert_called_once_with("LS-001", exclude_archived=True)

    def test_create_order_duplicate_vessel_code_raises(self, order_service, order_repo_mock):
        """Дубликат кода сосуда — ValueError."""
        order_repo_mock.vessel_code_exists.return_value = True

        with pytest.raises(ValueError, match="уже используется"):
            order_service.create_order("LS-001", 1, 1, [1], 1000)

    def test_create_order_invalid_client_id_raises(self, order_service):
        """Некорректный ID клиента — ValueError."""
        with pytest.raises(ValueError, match="Клиент обязателен"):
            order_service.create_order("LS-001", 0, 1, [1], 1000)
        with pytest.raises(ValueError, match="Клиент обязателен"):
            order_service.create_order("LS-001", -1, 1, [1], 1000)

    def test_create_order_invalid_employee_id_raises(self, order_service):
        """Некорректный ID сотрудника — ValueError."""
        with pytest.raises(ValueError, match="Сотрудник обязателен"):
            order_service.create_order("LS-001", 1, 0, [1], 1000)

    def test_create_order_empty_services_raises(self, order_service):
        """Пустой список услуг — ValueError."""
        with pytest.raises(ValueError, match="хотя бы одну услугу"):
            order_service.create_order("LS-001", 1, 1, [], 1000)


class TestOrderServiceUpdate:
    """Тесты обновления заказа (делегирование в репозиторий)."""

    def test_update_order(self, order_service, order_repo_mock):
        """Обновление заказа - требует все поля."""
        order_repo_mock.vessel_code_exists.return_value = False

        order_service.update_order(
            order_id=1,
            vessel_code="LS-002",
            client_id=1,
            employee_id=1,
            service_ids=[1, 2],
            total_price=20000.00,
        )

        order_repo_mock.update_order.assert_called_once_with(
            order_id=1,
            vessel_code="LS-002",
            client_id=1,
            employee_id=1,
            service_ids=[1, 2],
            total_price=20000.00,
        )

    def test_update_order_duplicate_vessel_code_raises(self, order_service, order_repo_mock):
        """Дубликат vessel_code при обновлении — ValueError."""
        order_repo_mock.vessel_code_exists.return_value = True

        with pytest.raises(ValueError, match="уже используется"):
            order_service.update_order(
                order_id=1, vessel_code="LS-001", client_id=1, employee_id=1, service_ids=[1], total_price=1000
            )

    def test_update_order_invalid_order_id_raises(self, order_service):
        """Некорректный ID заказа — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID заказа"):
            order_service.update_order(0, "LS-001", 1, 1, [1], 1000)

    def test_update_order_empty_vessel_code_raises(self, order_service):
        """Пустой vessel_code — ValueError."""
        with pytest.raises(ValueError, match="Код сосуда обязателен"):
            order_service.update_order(1, "", 1, 1, [1], 1000)

    def test_update_order_invalid_client_raises(self, order_service):
        """Некорректный клиент — ValueError."""
        with pytest.raises(ValueError, match="Клиент обязателен"):
            order_service.update_order(1, "LS-001", 0, 1, [1], 1000)

    def test_update_order_invalid_employee_raises(self, order_service):
        """Некорректный сотрудник — ValueError."""
        with pytest.raises(ValueError, match="Сотрудник обязателен"):
            order_service.update_order(1, "LS-001", 1, 0, [1], 1000)

    def test_update_order_empty_services_raises(self, order_service):
        """Пустой список услуг — ValueError."""
        with pytest.raises(ValueError, match="хотя бы одну услугу"):
            order_service.update_order(1, "LS-001", 1, 1, [], 1000)