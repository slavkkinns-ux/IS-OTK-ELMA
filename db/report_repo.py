"""Репозиторий отчётов, исследований и сотрудников (обратная совместимость).

Все функции deleгируют вызовам экземпляров ReportRepository и EmployeeRepository.
"""

from __future__ import annotations

from typing import Any

from db.repositories.employee_repository import EmployeeRepository
from db.repositories.report_repository import ReportRepository

_report_repo = ReportRepository()
_employee_repo = EmployeeRepository()


# =============================================================================
# ОЧЕРЕДЬ ИССЛЕДОВАНИЙ
# =============================================================================

def get_research_queue() -> list[dict[str, Any]]:
    """Очередь исследований (все услуги активных заказов)."""
    return _report_repo.get_research_queue()


def get_research_result(order_service_id: int) -> dict[str, Any] | None:
    """Получить результат исследования по order_service_id."""
    return _report_repo.get_research_result(order_service_id)


def save_research_result(
    order_service_id: int,
    employee_id: int,
    result_value: str,
    conclusion: str,
    result_date: Any,
) -> int:
    """Сохранить или обновить результат исследования. Возвращает research_id."""
    return _report_repo.save_research_result(
        order_service_id, employee_id, result_value, conclusion, result_date
    )


# =============================================================================
# ИССЛЕДОВАНИЯ ПО ЗАКАЗУ (для вкладки «Отчёты»)
# =============================================================================

def get_report_research(order_id: int) -> list[dict[str, Any]]:
    """Исследования по конкретному заказу (для таблицы в отчёте)."""
    return _report_repo.get_report_research(order_id)


# =============================================================================
# ОТЧЁТЫ
# =============================================================================

def get_recent_reports(limit: int = 10) -> list[dict[str, Any]]:
    """Последние отчёты."""
    return _report_repo.get_recent_reports(limit)


def get_report(report_id: int) -> dict[str, Any] | None:
    """Получить данные отчёта по ID."""
    return _report_repo.get_report(report_id)


def get_report_by_order(order_id: int) -> dict[str, Any] | None:
    """Получить последний отчёт по заказу (для проверки дубликата)."""
    return _report_repo.get_report_by_order(order_id)


def create_report(order_id: int, employee_id: int, file_path: str) -> int:
    """Создать запись отчёта в БД. Возвращает report_id."""
    return _report_repo.create_report(order_id, employee_id, file_path)


def get_next_report_number() -> int:
    """Получить следующий номер отчёта."""
    return _report_repo.get_next_report_number()


def get_report_by_path(file_path: str) -> dict[str, Any] | None:
    """Найти отчёт по пути к файлу."""
    return _report_repo.get_report_by_path(file_path)


def delete_report(report_id: int) -> None:
    """Удалить отчёт из базы данных."""
    _report_repo.delete_report(report_id)


def update_report_path(report_id: int, file_path: str) -> None:
    """Обновить путь к файлу отчёта."""
    _report_repo.update_report_path(report_id, file_path)


# =============================================================================
# Employee Repository (ранее была здесь, вынесена в employee_repository.py)
# =============================================================================

def get_all_employees(
    role_filter: str | None = None,
    active_only: bool = False,
    search_query: str | None = None,
) -> list[dict[str, Any]]:
    """Получить список сотрудников с фильтрацией."""
    return _employee_repo.get_all_employees(
        role_filter=role_filter, active_only=active_only, search_query=search_query
    )


def get_employee(employee_id: int) -> dict[str, Any] | None:
    """Получить сотрудника по ID."""
    return _employee_repo.get_employee(employee_id)


def create_employee(
    full_name: str,
    login: str,
    password: str,
    role: str,
    is_active: bool = True,
    email: str | None = None,
    phone: str | None = None,
    created_by: int | None = None,
) -> int:
    """Создать нового сотрудника. Возвращает employee_id."""
    return _employee_repo.create_employee(
        full_name=full_name,
        login=login,
        password=password,
        role=role,
        is_active=is_active,
        email=email,
        phone=phone,
        created_by=created_by,
    )


def update_employee(
    employee_id: int,
    full_name: str | None = None,
    login: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    email: str | None = None,
    phone: str | None = None,
) -> bool:
    """Обновить данные сотрудника."""
    return _employee_repo.update_employee(
        employee_id=employee_id,
        full_name=full_name,
        login=login,
        role=role,
        is_active=is_active,
        email=email,
        phone=phone,
    )


def reset_password(employee_id: int, new_password: str = "123456") -> bool:
    """Сбросить пароль сотрудника."""
    return _employee_repo.reset_password(employee_id, new_password)


def get_employee_stats() -> dict[str, Any]:
    """Получить статистику по сотрудникам."""
    return _employee_repo.get_employee_stats()


def check_login_exists(
    login: str, exclude_employee_id: int | None = None
) -> bool:
    """Проверить, существует ли логин."""
    return _employee_repo.check_login_exists(login, exclude_employee_id)


__all__ = [
    # Исследования
    "get_research_queue",
    "get_research_result",
    "save_research_result",
    # Исследования по заказу
    "get_report_research",
    # Отчёты
    "get_recent_reports",
    "get_report",
    "get_report_by_order",
    "create_report",
    "get_next_report_number",
    "get_report_by_path",
    "delete_report",
    "update_report_path",
    # Сотрудники
    "get_all_employees",
    "get_employee",
    "create_employee",
    "update_employee",
    "reset_password",
    "get_employee_stats",
    "check_login_exists",
]
