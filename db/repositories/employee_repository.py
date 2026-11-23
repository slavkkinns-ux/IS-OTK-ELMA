"""Репозиторий сотрудников — доступ к данным о сотрудниках и их ролях."""

from __future__ import annotations

import hashlib
from typing import Any

from db.repositories.base import AbstractRepository


class EmployeeRepository(AbstractRepository):
    """Репозиторий сотрудников."""

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get_all_employees(
        self,
        role_filter: str | None = None,
        active_only: bool = False,
        search_query: str | None = None,
    ) -> list[dict[str, Any]]:
        """Получить список сотрудников с фильтрацией."""
        query = """
            SELECT
                e.employee_id, e.full_name, e.login, e.role, e.is_active,
                e.email, e.phone, e.last_login, e.created_at,
                e.created_by,
                (SELECT COUNT(*) FROM research_results rr
                 WHERE rr.employee_id = e.employee_id) AS research_count,
                (SELECT COUNT(*) FROM reports r
                 WHERE r.employee_id = e.employee_id) AS report_count
            FROM employees e
            WHERE 1=1
        """
        params: list[Any] = []

        if role_filter:
            query += " AND e.role = %s"
            params.append(role_filter)

        if active_only:
            query += " AND e.is_active = 1"

        if search_query:
            query += " AND (e.full_name LIKE %s OR e.login LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])

        query += " ORDER BY e.full_name"
        return self.fetch_all(query, tuple(params))

    def get_employee(self, employee_id: int) -> dict[str, Any] | None:
        """Получить сотрудника по ID."""
        query = """
            SELECT
                e.employee_id, e.full_name, e.login, e.role, e.is_active,
                e.must_change_password, e.email, e.phone, e.last_login, e.created_at,
                e.created_by
            FROM employees e
            WHERE e.employee_id = %s
        """
        return self.fetch_one(query, (employee_id,))

    def get_employee_by_login(
        self, login: str, password_hash: str
    ) -> dict[str, Any] | None:
        """Найти сотрудника по логину и хешу пароля (для авторизации)."""
        query = """
            SELECT
                e.employee_id, e.full_name, e.login, e.role, e.is_active
            FROM employees e
            WHERE e.login = %s AND e.password_hash = %s AND e.is_active = 1
        """
        return self.fetch_one(query, (login, password_hash))

    # ------------------------------------------------------------------
    # Создание / обновление / удаление
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
        """Создать нового сотрудника. Возвращает employee_id."""
        password_hash = hashlib.sha256(password.encode("utf-8")).hexdigest()

        with self.db.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO employees
                        (full_name, login, password_hash, role, is_active,
                         must_change_password, email, phone, created_at, created_by)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
                    """,
                    (
                        full_name, login, password_hash, role,
                        1 if is_active else 0, 1, email, phone, created_by,
                    ),
                )
                return int(cur.lastrowid)

    def update_employee(
        self,
        employee_id: int,
        full_name: str | None = None,
        login: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        email: str | None = None,
        phone: str | None = None,
    ) -> bool:
        """Обновить данные сотрудника. Возвращает True, если строка была обновлена."""
        updates: list[str] = []
        params: list[Any] = []

        if full_name is not None:
            updates.append("full_name = %s")
            params.append(full_name)
        if login is not None:
            updates.append("login = %s")
            params.append(login)
        if role is not None:
            updates.append("role = %s")
            params.append(role)
        if is_active is not None:
            updates.append("is_active = %s")
            params.append(1 if is_active else 0)
        if email is not None:
            updates.append("email = %s")
            params.append(email)
        if phone is not None:
            updates.append("phone = %s")
            params.append(phone)

        if not updates:
            return False

        params.append(employee_id)
        query = f"UPDATE employees SET {', '.join(updates)} WHERE employee_id = %s"

        with self.db.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(query, params)
                return cur.rowcount > 0

    def reset_password(
        self, employee_id: int, new_password: str = "123456"
    ) -> bool:
        """Сбросить пароль сотрудника. Возвращает True, если строка была обновлена."""
        password_hash = hashlib.sha256(new_password.encode("utf-8")).hexdigest()

        with self.db.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE employees
                    SET password_hash = %s, must_change_password = 1
                    WHERE employee_id = %s
                    """,
                    (password_hash, employee_id),
                )
                return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Статистика и проверки
    # ------------------------------------------------------------------

    def get_employee_stats(self) -> dict[str, Any]:
        """Получить статистику по сотрудникам."""
        row = self.fetch_one("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active,
                SUM(CASE WHEN role = 'manager' THEN 1 ELSE 0 END) AS managers,
                SUM(CASE WHEN role = 'lab_technician' THEN 1 ELSE 0 END) AS lab_technicians,
                SUM(CASE WHEN role = 'controller' THEN 1 ELSE 0 END) AS controllers,
                SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) AS admins
            FROM employees
        """)
        if not row:
            return {
                "total": 0, "active": 0, "managers": 0,
                "lab_technicians": 0, "controllers": 0, "admins": 0,
            }
        return {
            "total": int(row["total"] or 0),
            "active": int(row["active"] or 0),
            "managers": int(row["managers"] or 0),
            "lab_technicians": int(row["lab_technicians"] or 0),
            "controllers": int(row["controllers"] or 0),
            "admins": int(row["admins"] or 0),
        }

    def check_login_exists(
        self, login: str, exclude_employee_id: int | None = None
    ) -> bool:
        """Проверить, существует ли логин."""
        if exclude_employee_id is not None:
            query = """
                SELECT COUNT(*) AS cnt FROM employees
                WHERE login = %s AND employee_id != %s
            """
            row = self.fetch_one(query, (login, exclude_employee_id))
        else:
            query = "SELECT COUNT(*) AS cnt FROM employees WHERE login = %s"
            row = self.fetch_one(query, (login,))
        return int(row["cnt"] or 0) > 0 if row else False


__all__ = ["EmployeeRepository"]
