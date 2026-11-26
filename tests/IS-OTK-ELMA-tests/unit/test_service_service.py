"""Unit-тесты для ServiceService."""

from __future__ import annotations

import pytest

from services.service_service import ServiceService


class TestServiceServiceRead:
    """Тесты чтения услуг."""

    def test_get_all_services_active_only(self, service_service, service_repo_mock):
        """Только активные услуги."""
        service_repo_mock.get_all_services.return_value = [
            {"service_id": 1, "service_name": "Активная", "is_active": 1}
        ]

        result = service_service.get_all_services(include_inactive=False)

        assert len(result) == 1
        service_repo_mock.get_all_services.assert_called_once_with(include_inactive=False)

    def test_get_all_services_include_inactive(self, service_service, service_repo_mock):
        """Включая неактивные."""
        service_repo_mock.get_all_services.return_value = [
            {"service_id": 1, "is_active": 1},
            {"service_id": 2, "is_active": 0},
        ]

        result = service_service.get_all_services(include_inactive=True)

        assert len(result) == 2
        service_repo_mock.get_all_services.assert_called_once_with(include_inactive=True)

    def test_service_name_exists_true(self, service_service, service_repo_mock):
        """Название существует."""
        service_repo_mock.service_name_exists.return_value = True

        result = service_service.service_name_exists("Тест услуга")

        assert result is True

    def test_service_name_exists_false(self, service_service, service_repo_mock):
        """Название не существует."""
        service_repo_mock.service_name_exists.return_value = False

        result = service_service.service_name_exists("Несуществующая")

        assert result is False

    def test_service_name_exists_empty_raises(self, service_service):
        """Пустое название — ValueError."""
        with pytest.raises(ValueError, match="Название услуги обязательно"):
            service_service.service_name_exists("")
        with pytest.raises(ValueError, match="Название услуги обязательно"):
            service_service.service_name_exists("   ")

    def test_service_name_exists_trims(self, service_service, service_repo_mock):
        """Название обрезается."""
        service_repo_mock.service_name_exists.return_value = False

        service_service.service_name_exists("  Тест  ")

        service_repo_mock.service_name_exists.assert_called_once_with("Тест", None)

    def test_is_service_used_true(self, service_service, service_repo_mock):
        """Услуга используется."""
        service_repo_mock.is_service_used.return_value = True

        result = service_service.is_service_used(1)

        assert result is True

    def test_is_service_used_false(self, service_service, service_repo_mock):
        """Услуга не используется."""
        service_repo_mock.is_service_used.return_value = False

        result = service_service.is_service_used(1)

        assert result is False

    def test_is_service_used_invalid_id_raises(self, service_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID услуги"):
            service_service.is_service_used(0)
        with pytest.raises(ValueError, match="Некорректный ID услуги"):
            service_service.is_service_used(-1)


class TestServiceServiceCreate:
    """Тесты создания услуги."""

    def test_add_service_success(self, service_service, service_repo_mock):
        """Успешное создание услуги."""
        service_repo_mock.service_name_exists.return_value = False
        service_repo_mock.add_service.return_value = 42

        service_id = service_service.add_service("Новая услуга", 5000.00)

        assert service_id == 42
        service_repo_mock.add_service.assert_called_once_with("Новая услуга", 5000.00)

    def test_add_service_empty_name_raises(self, service_service):
        """Пустое название — ValueError."""
        with pytest.raises(ValueError, match="Введите название услуги"):
            service_service.add_service("", 1000)

    def test_add_service_short_name_raises(self, service_service):
        """Короткое название — ValueError."""
        with pytest.raises(ValueError, match="минимум 3 символа"):
            service_service.add_service("ab", 1000)

    def test_add_service_duplicate_name_raises(self, service_service, service_repo_mock):
        """Дубликат названия — ValueError."""
        service_repo_mock.service_name_exists.return_value = True

        with pytest.raises(ValueError, match="уже существует"):
            service_service.add_service("Существующая", 1000)

    def test_add_service_none_price_raises(self, service_service):
        """None цена — ValueError."""
        with pytest.raises(ValueError, match="Введите цену\\."):
            service_service.add_service("Услуга", None)

    def test_add_service_invalid_price_format_raises(self, service_service):
        """Некорректный формат цены — ValueError."""
        with pytest.raises(ValueError, match="Некорректный формат цены\\."):
            service_service.add_service("Услуга", "не_число")

    def test_add_service_negative_price_raises(self, service_service):
        """Отрицательная цена — ValueError."""
        with pytest.raises(ValueError, match="Цена не может быть отрицательной\\."):
            service_service.add_service("Услуга", -100)

    def test_add_service_price_conversion(self, service_service, service_repo_mock):
        """Цена конвертируется в float."""
        service_repo_mock.service_name_exists.return_value = False
        service_repo_mock.add_service.return_value = 1

        service_service.add_service("Услуга", "5000")  # строка

        call_args = service_repo_mock.add_service.call_args
        assert call_args[0][1] == 5000.0  # float


class TestServiceServiceUpdate:
    """Тесты обновления услуги."""

    def test_update_service_success(self, service_service, service_repo_mock):
        """Успешное обновление."""
        service_repo_mock.service_name_exists.return_value = False

        service_service.update_service(1, "Обновлённая", 7500.00, is_active=1)

        service_repo_mock.update_service.assert_called_once_with(
            service_id=1, service_name="Обновлённая", price=7500.00, is_active=1
        )

    def test_update_service_invalid_id_raises(self, service_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID услуги"):
            service_service.update_service(0, "Name", 1000)

    def test_update_service_empty_name_raises(self, service_service):
        """Пустое название — ValueError."""
        with pytest.raises(ValueError, match="Введите название услуги"):
            service_service.update_service(1, "", 1000)

    def test_update_service_short_name_raises(self, service_service):
        """Короткое название — ValueError."""
        with pytest.raises(ValueError, match="минимум 3 символа"):
            service_service.update_service(1, "ab", 1000)

    def test_update_service_duplicate_name_raises(self, service_service, service_repo_mock):
        """Дубликат названия (кроме себя) — ValueError."""
        service_repo_mock.service_name_exists.return_value = True

        with pytest.raises(ValueError, match="уже существует"):
            service_service.update_service(1, "Существующая", 1000)

    def test_update_service_invalid_price_raises(self, service_service):
        """Некорректная цена — ValueError (валидация названия проходит первой)."""
        with pytest.raises(ValueError, match="Некорректный формат цены\\."):
            service_service.update_service(1, "Valid Name", "bad")

    def test_update_service_negative_price_raises(self, service_service):
        """Отрицательная цена — ValueError."""
        with pytest.raises(ValueError, match="Цена не может быть отрицательной\\."):
            service_service.update_service(1, "Valid Name", -1)


class TestServiceServiceDelete:
    """Тесты удаления услуги."""

    def test_delete_service_soft(self, service_service, service_repo_mock):
        """Мягкое удаление."""
        service_service.delete_service(1, soft=True)

        service_repo_mock.delete_service.assert_called_once_with(service_id=1, soft=True)

    def test_delete_service_hard_not_used(self, service_service, service_repo_mock):
        """Жёсткое удаление — услуга не используется."""
        service_repo_mock.is_service_used.return_value = False

        service_service.delete_service(1, soft=False)

        service_repo_mock.delete_service.assert_called_once_with(service_id=1, soft=False)

    def test_delete_service_hard_used_raises(self, service_service, service_repo_mock):
        """Жёсткое удаление используемой услуги — ValueError."""
        service_repo_mock.is_service_used.return_value = True

        with pytest.raises(ValueError, match="используется в существующих заказах"):
            service_service.delete_service(1, soft=False)


class TestServiceServiceToggle:
    """Тесты переключения статуса."""

    def test_toggle_service_active_to_inactive(self, service_service, service_repo_mock):
        """Активная -> неактивная."""
        service_repo_mock.get_all_services.return_value = [
            {"service_id": 1, "service_name": "Тест", "price": 1000, "is_active": 1}
        ]

        new_status = service_service.toggle_service(1)

        assert new_status == 0
        service_repo_mock.update_service.assert_called_once_with(
            service_id=1, service_name="Тест", price=1000.0, is_active=0
        )

    def test_toggle_service_inactive_to_active(self, service_service, service_repo_mock):
        """Неактивная -> активная."""
        service_repo_mock.get_all_services.return_value = [
            {"service_id": 1, "service_name": "Тест", "price": 1000, "is_active": 0}
        ]

        new_status = service_service.toggle_service(1)

        assert new_status == 1
        service_repo_mock.update_service.assert_called_once_with(
            service_id=1, service_name="Тест", price=1000.0, is_active=1
        )

    def test_toggle_service_invalid_id_raises(self, service_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID услуги"):
            service_service.toggle_service(0)

    def test_toggle_service_not_found_raises(self, service_service, service_repo_mock):
        """Услуга не найдена — ValueError."""
        service_repo_mock.get_all_services.return_value = []

        with pytest.raises(ValueError, match="не найдена"):
            service_service.toggle_service(999)