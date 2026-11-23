"""Сервис сотрудников — бизнес-логика управления персоналом.

Содержит всю бизнес-логику, ранее находившуюся в pages/employees_page.py:
валидация логина, защита админов, хеширование пароля, проверка прав доступа.
Все методы принимают employee_id, а не весь объект сотрудника.
"""

from __future__ import annotations

from typing import Any

from db.repositories.employee_repository import EmployeeRepository

from services.base_service import BaseService


class EmployeeService(BaseService):
    """Сервис для управления сотрудниками.

    Принимает репозиторий через конструктор (dependency injection).
    Не содержит прямых SQL-запросов и не зависит от UI.
    """

    def __init__(self, employee_repo: EmployeeRepository) -> None:
        self.repo = employee_repo
        super().__init__()

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get_employees(
        self,
        role_filter: str | None = None,
        active_only: bool = False,
        search_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """Получить список сотрудников с фильтрацией.

        Args:
            role_filter: Фильтр по роли (manager, lab_technician, controller, admin).
            active_only: Если True — только активные сотрудники.
            search_query: Поиск по ФИО или логину.

        Returns:
            Список словарей с данными сотрудников.
        """
        return self.repo.get_all_employees(
            role_filter=role_filter,
            active_only=active_only,
            search_query=search_query,
        )

    def get_employee_by_id(self, employee_id: int) -> dict[str, Any] | None:
        """Получить сотрудника по ID.

        Args:
            employee_id: ID сотрудника.

        Returns:
            Словарь с данными сотрудника или None, если не найден.

        Raises:
            ValueError: Если employee_id некорректен.
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        return self.repo.get_employee(employee_id)

    def get_employee_stats(self) -> dict[str, Any]:
        """Получить статистику по сотрудникам.

        Returns:
            Словарь с количеством всего, активных, менеджеров, лаборантов,
            контролёров и администраторов.
        """
        return self.repo.get_employee_stats()

    # ------------------------------------------------------------------
    # Создание
    # ------------------------------------------------------------------

    def create_employee(
        self,
        full_name: str,
        login: str,
        password: str,
        role: str,
        is_active: bool = True,
        email: str | None = None,
        phone: str | None = None,
        created_by: int | None = None,
    ) -> int:
        """Создать нового сотрудника с валидацией входных данных.

        Args:
            full_name: ФИО сотрудника.
            login: Логин для входа (мин. 3 символа, уникальный).
            password: Пароль (мин. 6 символов).
            role: Роль сотрудника.
            is_active: Активен ли сотрудник.
            email: Email (опционально).
            phone: Телефон (опционально).
            created_by: ID сотрудника, создавшего запись.

        Returns:
            ID созданного сотрудника.

        Raises:
            ValueError: При некорректных входных данных или дубле логина.
        """
        # Валидация ФИО
        if not full_name or not full_name.strip():
            raise ValueError("ФИО обязательно для заполнения")
        full_name = full_name.strip()

        # Валидация логина
        if not login or not login.strip():
            raise ValueError("Логин обязателен для заполнения")
        login = login.strip()
        if len(login) < 3:
            raise ValueError("Логин должен содержать минимум 3 символа")

        # Проверка уникальности логина
        if self.repo.check_login_exists(login):
            raise ValueError(f"Логин '{login}' уже занят другим сотрудником")

        # Валидация пароля
        if not password or len(password) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")

        if not role:
            raise ValueError("Роль обязательна")

        # Хеширование пароля выполняется внутри репозитория
        employee_id = self.repo.create_employee(
            full_name=full_name,
            login=login,
            password=password,
            role=role,
            is_active=is_active,
            email=email,
            phone=phone,
            created_by=created_by,
        )

        self.log_action("create_employee", int(employee_id), created_by or 0)
        return int(employee_id)

    # ------------------------------------------------------------------
    # Обновление
    # ------------------------------------------------------------------

    def update_employee(
        self,
        employee_id: int,
        current_user_id: int,
        full_name: str | None = None,
        login: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> bool:
        """Обновить данные сотрудника с проверкой прав доступа.

        Args:
            employee_id: ID редактируемого сотрудника.
            current_user_id: ID текущего пользователя (выполняющего действие).
            full_name: Новое ФИО (опционально).
            login: Новый логин (опционально).
            role: Новая роль (опционально).
            is_active: Новый статус активности (опционально).
            email: Новый email (опционально).
            phone: Новый телефон (опционально).

        Returns:
            True, если запись была обновлена, False — если нет изменений.

        Raises:
            ValueError: Если сотрудник не найден или данные некорректны.
            PermissionError: Если пытаются изменить другого администратора.
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        if not isinstance(current_user_id, int) or current_user_id <= 0:
            raise ValueError(f"Некорректный ID текущего пользователя: {current_user_id}")

        emp = self.repo.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")

        # Защита: нельзя менять данные другого администратора
        if (
            employee_id != current_user_id
            and emp.get("role") == "admin"
        ):
            self.logger.warning(
                "Попытка изменения другого администратора: target_id=%s, current_user_id=%s",
                employee_id, current_user_id,
            )
            raise PermissionError(
                "Нельзя изменять данные другого администратора. "
                "Редактировать можно только свою учётную запись."
            )

        # Защита: последний активный администратор не может понизить свою роль
        if (
            employee_id == current_user_id
            and role is not None
            and role != "admin"
            and emp.get("role") == "admin"
        ):
            active_admins = self.repo.get_all_employees(
                role_filter="admin", active_only=True
            )
            if len(active_admins) <= 1:
                raise PermissionError(
                    "Вы последний активный администратор системы. "
                    "Нельзя изменить свою роль, пока не создан другой администратор."
                )

        # Валидация логина, если он меняется
        if login is not None:
            login = login.strip()
            if not login:
                raise ValueError("Логин не может быть пустым")
            if len(login) < 3:
                raise ValueError("Логин должен содержать минимум 3 символа")
            if login != emp.get("login", ""):
                if self.repo.check_login_exists(login, exclude_employee_id=employee_id):
                    raise ValueError(f"Логин '{login}' уже занят другим сотрудником")

        result = self.repo.update_employee(
            employee_id=employee_id,
            full_name=full_name,
            login=login,
            role=role,
            is_active=is_active,
            email=email,
            phone=phone,
        )

        if result:
            self.log_action("update_employee", employee_id, current_user_id)
        return result

    # ------------------------------------------------------------------
    # Статус / деактивация
    # ------------------------------------------------------------------

    def deactivate_employee(self, employee_id: int, current_user_id: int) -> None:
        """Деактивировать сотрудника с проверкой прав.

        Args:
            employee_id: ID сотрудника для деактивации.
            current_user_id: ID текущего пользователя.

        Raises:
            ValueError: Если сотрудник не найден или ID некорректен.
            PermissionError: Если нельзя деактивировать (другой админ, последний админ, себя).
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        if not isinstance(current_user_id, int) or current_user_id <= 0:
            raise ValueError(f"Некорректный ID текущего пользователя: {current_user_id}")

        if employee_id == current_user_id:
            raise PermissionError("Нельзя деактивировать самого себя")

        emp = self.repo.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")

        # Проверка: нельзя деактивировать другого администратора
        if emp.get("role") == "admin" and emp.get("employee_id") != current_user_id:
            self.logger.warning(
                "Попытка деактивации другого администратора: target_id=%s, current_user_id=%s",
                employee_id, current_user_id,
            )
            raise PermissionError(
                "Нельзя деактивировать другого администратора. "
                "Изменить статус можно только для своей учётной записи."
            )

        # Защита последнего активного администратора
        if emp.get("role") == "admin" and emp.get("is_active", False):
            active_admins = self.repo.get_all_employees(
                role_filter="admin", active_only=True
            )
            if len(active_admins) <= 1:
                raise PermissionError(
                    "Нельзя деактивировать последнего активного администратора. "
                    "Система должна иметь хотя бы одного активного администратора."
                )

        self.repo.update_employee(employee_id, is_active=False)
        self.log_action("deactivate_employee", employee_id, current_user_id)

    def activate_employee(self, employee_id: int, current_user_id: int) -> None:
        """Активировать сотрудника.

        Args:
            employee_id: ID сотрудника для активации.
            current_user_id: ID текущего пользователя.

        Raises:
            ValueError: Если сотрудник не найден или ID некорректен.
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        if not isinstance(current_user_id, int) or current_user_id <= 0:
            raise ValueError(f"Некорректный ID текущего пользователя: {current_user_id}")

        emp = self.repo.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")

        self.repo.update_employee(employee_id, is_active=True)
        self.log_action("activate_employee", employee_id, current_user_id)

    def toggle_employee_status(self, employee_id: int, current_user_id: int) -> bool:
        """Переключить статус сотрудника с проверкой прав.

        Args:
            employee_id: ID сотрудника.
            current_user_id: ID текущего пользователя.

        Returns:
            Новый статус (True — активен, False — деактивирован).

        Raises:
            ValueError: Если сотрудник не найден или ID некорректен.
            PermissionError: Если нельзя изменить статус.
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        if not isinstance(current_user_id, int) or current_user_id <= 0:
            raise ValueError(f"Некорректный ID текущего пользователя: {current_user_id}")

        emp = self.repo.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")

        # Защита: нельзя изменить статус другого администратора
        if emp.get("role") == "admin" and emp.get("employee_id") != current_user_id:
            self.logger.warning(
                "Попытка изменения статуса другого администратора: "
                "target_id=%s, current_user_id=%s",
                employee_id, current_user_id,
            )
            raise PermissionError(
                "Нельзя изменить статус другого администратора. "
                "Изменить можно только свою учётную запись."
            )

        is_active = bool(emp.get("is_active", False))
        new_status = not is_active

        # Защита последнего активного администратора при деактивации
        if emp.get("role") == "admin" and not new_status:
            active_admins = self.repo.get_all_employees(
                role_filter="admin", active_only=True
            )
            if len(active_admins) <= 1:
                raise PermissionError(
                    "Нельзя деактивировать последнего активного администратора!"
                )

        self.repo.update_employee(employee_id, is_active=new_status)
        action = "activate_employee" if new_status else "deactivate_employee"
        self.log_action(action, employee_id, current_user_id)
        return new_status

    # ------------------------------------------------------------------
    # Сброс пароля
    # ------------------------------------------------------------------

    def reset_password(
        self, employee_id: int, current_user_id: int, new_password: str = "123456"
    ) -> bool:
        """Сбросить пароль сотрудника.

        Args:
            employee_id: ID сотрудника.
            current_user_id: ID текущего пользователя (инициировавшего сброс).
            new_password: Новый пароль (по умолчанию '123456').

        Returns:
            True, если пароль был сброшен, False — если сотрудник не найден.

        Raises:
            ValueError: Если пароль слишком короткий или ID некорректен.
        """
        if not isinstance(employee_id, int) or employee_id <= 0:
            raise ValueError(f"Некорректный ID сотрудника: {employee_id}")
        if not isinstance(current_user_id, int) or current_user_id <= 0:
            raise ValueError(f"Некорректный ID текущего пользователя: {current_user_id}")

        emp = self.repo.get_employee(employee_id)
        if not emp:
            raise ValueError(f"Сотрудник с ID {employee_id} не найден")

        if not new_password or len(new_password) < 6:
            raise ValueError("Пароль должен содержать минимум 6 символов")

        result = self.repo.reset_password(employee_id, new_password)
        if result:
            self.log_action("reset_password", employee_id, current_user_id)
        return result

    # ------------------------------------------------------------------
    # Аутентификация
    # ------------------------------------------------------------------

    def authenticate_employee(
        self, login: str, password: str
    ) -> dict[str, Any] | None:
        """Аутентифицировать сотрудника по логину и паролю.

        Args:
            login: Логин сотрудника.
            password: Пароль в открытом виде.

        Returns:
            Данные сотрудника или None, если аутентификация не удалась.
        """
        if not login or not login.strip():
            raise ValueError("Логин обязателен")
        if not password:
            raise ValueError("Пароль обязателен")

        login = login.strip()
        import hashlib
        password_hash = hashlib.sha256(password.encode()).hexdigest()

        emp = self.repo.get_employee_by_login(login, password_hash)
        if emp:
            self.logger.info(
                "Сотрудник авторизован: id=%s, login=%s",
                emp.get("employee_id"), login,
            )
        return emp


__all__ = ["EmployeeService"]
