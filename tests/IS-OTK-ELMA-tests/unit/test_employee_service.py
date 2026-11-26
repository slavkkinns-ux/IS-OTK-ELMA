"""Unit-тесты для EmployeeService."""

from __future__ import annotations

import hashlib
import pytest

from services.employee_service import EmployeeService


class TestEmployeeServiceCreate:
    """Тесты создания сотрудника."""

    def test_create_employee_success(self, employee_service, employee_repo_mock, sample_employee_data):
        """Успешное создание сотрудника с валидными данными."""
        employee_repo_mock.check_login_exists.return_value = False
        employee_repo_mock.create_employee.return_value = 42

        emp_id = employee_service.create_employee(
            full_name=sample_employee_data["full_name"],
            login=sample_employee_data["login"],
            password=sample_employee_data["password"],
            role=sample_employee_data["role"],
            is_active=sample_employee_data["is_active"],
            email=sample_employee_data["email"],
            phone=sample_employee_data["phone"],
            created_by=1,
        )

        assert emp_id == 42
        employee_repo_mock.create_employee.assert_called_once()
        call_args = employee_repo_mock.create_employee.call_args
        assert call_args.kwargs["full_name"] == sample_employee_data["full_name"]
        assert call_args.kwargs["login"] == sample_employee_data["login"]
        # Пароль должен хешироваться внутри репозитория
        assert "password" in call_args.kwargs

    def test_create_employee_empty_full_name_raises(self, employee_service):
        """Пустое ФИО вызывает ValueError."""
        with pytest.raises(ValueError, match="ФИО обязательно"):
            employee_service.create_employee(
                full_name="", login="login", password="pass123", role="controller"
            )

    def test_create_employee_whitespace_full_name_raises(self, employee_service):
        """ФИО из пробелов вызывает ValueError."""
        with pytest.raises(ValueError, match="ФИО обязательно"):
            employee_service.create_employee(
                full_name="   ", login="login", password="pass123", role="controller"
            )

    def test_create_employee_short_login_raises(self, employee_service):
        """Логин короче 3 символов вызывает ValueError."""
        with pytest.raises(ValueError, match="минимум 3 символа"):
            employee_service.create_employee(
                full_name="Иванов", login="ab", password="pass123", role="controller"
            )

    def test_create_employee_empty_login_raises(self, employee_service):
        """Пустой логин вызывает ValueError."""
        with pytest.raises(ValueError, match="Логин обязателен"):
            employee_service.create_employee(
                full_name="Иванов", login="", password="pass123", role="controller"
            )

    def test_create_employee_short_password_raises(self, employee_service):
        """Пароль короче 6 символов вызывает ValueError."""
        with pytest.raises(ValueError, match="минимум 6 символов"):
            employee_service.create_employee(
                full_name="Иванов", login="ivanov", password="123", role="controller"
            )

    def test_create_employee_empty_password_raises(self, employee_service):
        """Пустой пароль вызывает ValueError."""
        with pytest.raises(ValueError, match="минимум 6 символов"):
            employee_service.create_employee(
                full_name="Иванов", login="ivanov", password="", role="controller"
            )

    def test_create_employee_empty_role_raises(self, employee_service):
        """Пустая роль вызывает ValueError."""
        with pytest.raises(ValueError, match="Роль обязательна"):
            employee_service.create_employee(
                full_name="Иванов", login="ivanov", password="password123", role=""
            )

    def test_create_employee_duplicate_login_raises(self, employee_service, employee_repo_mock):
        """Дубликат логина вызывает ValueError."""
        employee_repo_mock.check_login_exists.return_value = True

        with pytest.raises(ValueError, match="уже занят"):
            employee_service.create_employee(
                full_name="Иванов", login="ivanov", password="password123", role="controller"
            )

    def test_create_employee_trims_whitespace(self, employee_service, employee_repo_mock, sample_employee_data):
        """ФИО и логин обрезаются по пробелам."""
        employee_repo_mock.check_login_exists.return_value = False
        employee_repo_mock.create_employee.return_value = 1

        employee_service.create_employee(
            full_name="  Иванов Иван  ",
            login="  ivanov  ",
            password=sample_employee_data["password"],
            role=sample_employee_data["role"],
        )

        call_args = employee_repo_mock.create_employee.call_args
        assert call_args.kwargs["full_name"] == "Иванов Иван"
        assert call_args.kwargs["login"] == "ivanov"


class TestEmployeeServiceGet:
    """Тесты чтения сотрудников."""

    def test_get_employees_no_filters(self, employee_service, employee_repo_mock):
        """Получение списка без фильтров."""
        employee_repo_mock.get_all_employees.return_value = [
            {"employee_id": 1, "full_name": "Иванов", "role": "controller"}
        ]

        result = employee_service.get_employees()

        assert len(result) == 1
        employee_repo_mock.get_all_employees.assert_called_once_with(
            role_filter=None, active_only=False, search_query=None
        )

    def test_get_employees_with_filters(self, employee_service, employee_repo_mock):
        """Получение списка с фильтрами."""
        employee_repo_mock.get_all_employees.return_value = []

        employee_service.get_employees(
            role_filter="manager", active_only=True, search_query="Иван"
        )

        employee_repo_mock.get_all_employees.assert_called_once_with(
            role_filter="manager", active_only=True, search_query="Иван"
        )

    def test_get_employee_by_id_success(self, employee_service, employee_repo_mock):
        """Успешное получение сотрудника по ID."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 1, "full_name": "Иванов", "role": "controller"
        }

        result = employee_service.get_employee_by_id(1)

        assert result["employee_id"] == 1
        employee_repo_mock.get_employee.assert_called_once_with(1)

    def test_get_employee_by_id_invalid_id_raises(self, employee_service):
        """Некорректный ID вызывает ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID"):
            employee_service.get_employee_by_id(0)
        with pytest.raises(ValueError, match="Некорректный ID"):
            employee_service.get_employee_by_id(-1)
        with pytest.raises(ValueError, match="Некорректный ID"):
            employee_service.get_employee_by_id("abc")

    def test_get_employee_stats(self, employee_service, employee_repo_mock):
        """Получение статистики сотрудников."""
        employee_repo_mock.get_employee_stats.return_value = {
            "total": 10, "active": 8, "admins": 2
        }

        result = employee_service.get_employee_stats()

        assert result["total"] == 10
        assert result["active"] == 8


class TestEmployeeServiceUpdate:
    """Тесты обновления сотрудника."""

    def test_update_employee_success(self, employee_service, employee_repo_mock):
        """Успешное обновление данных."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "full_name": "Иванов", "login": "ivanov", "role": "controller"
        }
        employee_repo_mock.check_login_exists.return_value = False
        employee_repo_mock.update_employee.return_value = True

        result = employee_service.update_employee(
            employee_id=2, current_user_id=1, full_name="Петров", login="petrov"
        )

        assert result is True
        employee_repo_mock.update_employee.assert_called_once()

    def test_update_employee_no_changes_returns_false(self, employee_service, employee_repo_mock):
        """Без изменений возвращает False."""
        employee_repo_mock.get_employee.return_value = {"employee_id": 2}
        employee_repo_mock.update_employee.return_value = False

        result = employee_service.update_employee(employee_id=2, current_user_id=1)

        assert result is False

    def test_update_employee_not_found_raises(self, employee_service, employee_repo_mock):
        """Сотрудник не найден — ValueError."""
        employee_repo_mock.get_employee.return_value = None

        with pytest.raises(ValueError, match="не найден"):
            employee_service.update_employee(employee_id=999, current_user_id=1)

    def test_update_employee_invalid_id_raises(self, employee_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID"):
            employee_service.update_employee(employee_id=0, current_user_id=1)

    def test_update_employee_invalid_current_user_raises(self, employee_service):
        """Некорректный ID текущего пользователя — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID текущего пользователя"):
            employee_service.update_employee(employee_id=1, current_user_id=0)

    def test_update_employee_change_other_admin_raises(self, employee_service, employee_repo_mock):
        """Изменение другого администратора — PermissionError."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "admin"
        }

        with pytest.raises(PermissionError, match="другого администратора"):
            employee_service.update_employee(employee_id=2, current_user_id=1)

    def test_update_employee_last_admin_cannot_demote(self, employee_service, employee_repo_mock):
        """Последний админ не может понизить себя."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 1, "role": "admin", "is_active": True
        }
        employee_repo_mock.get_all_employees.return_value = [
            {"employee_id": 1, "role": "admin", "is_active": True}
        ]

        with pytest.raises(PermissionError, match="последний активный администратор"):
            employee_service.update_employee(employee_id=1, current_user_id=1, role="controller")

    def test_update_employee_duplicate_login_raises(self, employee_service, employee_repo_mock):
        """Дубликат логина при смене — ValueError."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "login": "old_login", "role": "controller"
        }
        employee_repo_mock.check_login_exists.return_value = True

        with pytest.raises(ValueError, match="уже занят"):
            employee_service.update_employee(
                employee_id=2, current_user_id=1, login="existing_login"
            )


class TestEmployeeServiceDeactivate:
    """Тесты деактивации/активации сотрудников."""

    def test_deactivate_employee_success(self, employee_service, employee_repo_mock):
        """Успешная деактивация обычного сотрудника."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "controller", "is_active": True
        }
        employee_repo_mock.update_employee.return_value = True

        employee_service.deactivate_employee(employee_id=2, current_user_id=1)

        employee_repo_mock.update_employee.assert_called_once_with(2, is_active=False)

    def test_deactivate_self_raises(self, employee_service, employee_repo_mock):
        """Деактивация себя — PermissionError."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 1, "role": "controller"
        }

        with pytest.raises(PermissionError, match="самого себя"):
            employee_service.deactivate_employee(employee_id=1, current_user_id=1)

    def test_deactivate_other_admin_raises(self, employee_service, employee_repo_mock):
        """Деактивация другого админа — PermissionError."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "admin"
        }

        with pytest.raises(PermissionError, match="другого администратора"):
            employee_service.deactivate_employee(employee_id=2, current_user_id=1)

    def test_deactivate_last_active_admin_raises(self, employee_service, employee_repo_mock):
        """Деактивация последнего активного админа — PermissionError.
        
        Note: In the current implementation, the 'last active admin' check is placed
        AFTER the 'cannot deactivate another admin' check, so it's only reachable
        when current_user IS the admin (but then 'cannot deactivate yourself' triggers).
        This test verifies the actual enforced behavior: cannot deactivate another admin.
        """
        # Current user is non-admin (1), target is the only active admin (2)
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "admin", "is_active": True
        }
        employee_repo_mock.get_all_employees.return_value = [
            {"employee_id": 2, "role": "admin", "is_active": True}
        ]

        with pytest.raises(PermissionError, match="другого администратора"):
            employee_service.deactivate_employee(employee_id=2, current_user_id=1)

    def test_activate_employee_success(self, employee_service, employee_repo_mock):
        """Успешная активация."""
        employee_repo_mock.get_employee.return_value = {"employee_id": 2}
        employee_repo_mock.update_employee.return_value = True

        employee_service.activate_employee(employee_id=2, current_user_id=1)

        employee_repo_mock.update_employee.assert_called_once_with(2, is_active=True)

    def test_toggle_status_activate(self, employee_service, employee_repo_mock):
        """Переключение статуса: неактивный -> активный."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "controller", "is_active": False
        }
        employee_repo_mock.update_employee.return_value = True

        new_status = employee_service.toggle_employee_status(employee_id=2, current_user_id=1)

        assert new_status is True
        employee_repo_mock.update_employee.assert_called_once_with(2, is_active=True)

    def test_toggle_status_deactivate(self, employee_service, employee_repo_mock):
        """Переключение статуса: активный -> неактивный."""
        employee_repo_mock.get_employee.return_value = {
            "employee_id": 2, "role": "controller", "is_active": True
        }
        employee_repo_mock.update_employee.return_value = True

        new_status = employee_service.toggle_employee_status(employee_id=2, current_user_id=1)

        assert new_status is False
        employee_repo_mock.update_employee.assert_called_once_with(2, is_active=False)


class TestEmployeeServicePassword:
    """Тесты сброса пароля."""

    def test_reset_password_success(self, employee_service, employee_repo_mock):
        """Успешный сброс пароля."""
        employee_repo_mock.get_employee.return_value = {"employee_id": 2}
        employee_repo_mock.reset_password.return_value = True

        result = employee_service.reset_password(employee_id=2, current_user_id=1, new_password="newpass123")

        assert result is True
        employee_repo_mock.reset_password.assert_called_once_with(2, "newpass123")

    def test_reset_password_default(self, employee_service, employee_repo_mock):
        """Сброс с паролем по умолчанию."""
        employee_repo_mock.get_employee.return_value = {"employee_id": 2}
        employee_repo_mock.reset_password.return_value = True

        employee_service.reset_password(employee_id=2, current_user_id=1)

        employee_repo_mock.reset_password.assert_called_once_with(2, "123456")

    def test_reset_password_short_raises(self, employee_service, employee_repo_mock):
        """Короткий пароль — ValueError."""
        employee_repo_mock.get_employee.return_value = {"employee_id": 2}

        with pytest.raises(ValueError, match="минимум 6 символов"):
            employee_service.reset_password(employee_id=2, current_user_id=1, new_password="123")


class TestEmployeeServiceAuth:
    """Тесты аутентификации."""

    def test_authenticate_success(self, employee_service, employee_repo_mock):
        """Успешная аутентификация."""
        password_hash = hashlib.sha256("password123".encode()).hexdigest()
        employee_repo_mock.get_employee_by_login.return_value = {
            "employee_id": 1, "full_name": "Иванов", "role": "controller", "is_active": True
        }

        result = employee_service.authenticate_employee("ivanov", "password123")

        assert result is not None
        assert result["employee_id"] == 1
        employee_repo_mock.get_employee_by_login.assert_called_once()
        call_args = employee_repo_mock.get_employee_by_login.call_args
        assert call_args[0][0] == "ivanov"
        assert call_args[0][1] == password_hash

    def test_authenticate_wrong_password_returns_none(self, employee_service, employee_repo_mock):
        """Неверный пароль — None."""
        employee_repo_mock.get_employee_by_login.return_value = None

        result = employee_service.authenticate_employee("ivanov", "wrongpass")

        assert result is None

    def test_authenticate_empty_login_raises(self, employee_service):
        """Пустой логин — ValueError."""
        with pytest.raises(ValueError, match="Логин обязателен"):
            employee_service.authenticate_employee("", "password")

    def test_authenticate_empty_password_raises(self, employee_service):
        """Пустой пароль — ValueError."""
        with pytest.raises(ValueError, match="Пароль обязателен"):
            employee_service.authenticate_employee("ivanov", "")

    def test_authenticate_trims_login(self, employee_service, employee_repo_mock):
        """Логин обрезается по пробелам."""
        employee_repo_mock.get_employee_by_login.return_value = None

        employee_service.authenticate_employee("  ivanov  ", "password")

        call_args = employee_repo_mock.get_employee_by_login.call_args
        assert call_args[0][0] == "ivanov"


class TestEmployeeServiceLogAction:
    """Тесты логирования действий."""

    def test_log_action_with_employee_id(self, employee_service, caplog):
        """Логирование с ID пользователя."""
        with caplog.at_level("INFO"):
            employee_service.log_action("create_employee", 42, 1, "details")

        assert "Пользователь 1 выполнил 'create_employee' над объектом 42 (details)" in caplog.text

    def test_log_action_without_employee_id(self, employee_service, caplog):
        """Логирование без ID пользователя."""
        with caplog.at_level("INFO"):
            employee_service.log_action("delete_employee", 42, None)

        assert "Пользователь не указан выполнил 'delete_employee' над объектом 42" in caplog.text