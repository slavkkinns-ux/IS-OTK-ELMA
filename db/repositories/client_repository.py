"""Репозиторий клиентов — доступ к данным о клиентах и их заказах/отчётах/результатах."""

from __future__ import annotations

from typing import Any

from db.repositories.base import AbstractRepository

# Общие SQL-фрагменты, чтобы не дублировать CASE-выражения во многих запросах.
_CLIENT_BASE_SELECT = """
    SELECT
        c.client_id,
        c.client_type,
        c.phone,
        c.email,
        c.is_active,
        c.created_at,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
             ELSE i.full_name END AS name,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
             ELSE i.full_name END AS full_name,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.director_name
             ELSE i.full_name END AS contact_person,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.address
             ELSE CONCAT(i.passport_series, ' ', i.passport_number) END AS details
    FROM clients c
    LEFT JOIN legal_entities le
        ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
    LEFT JOIN individuals i
        ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
"""

_CLIENT_DETAILS_SELECT = """
    SELECT
        c.*,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
             ELSE i.full_name END AS name,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.address ELSE NULL END AS address,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.inn ELSE NULL END AS inn,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.kpp ELSE NULL END AS kpp,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.checking_account ELSE NULL END AS bank_account,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.bik ELSE NULL END AS bik,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.director_name ELSE NULL END AS director_name,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.contact_person ELSE NULL END AS contact_person,
        CASE WHEN c.client_type = 'ФЛ' THEN i.full_name ELSE NULL END AS fl_name,
        CASE WHEN c.client_type = 'ФЛ' THEN i.birth_date ELSE NULL END AS birth_date,
        CASE WHEN c.client_type = 'ФЛ' THEN i.passport_series ELSE NULL END AS passport_series,
        CASE WHEN c.client_type = 'ФЛ' THEN i.passport_number ELSE NULL END AS passport_number
    FROM clients c
    LEFT JOIN legal_entities le
        ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
    LEFT JOIN individuals i
        ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
"""


class ClientRepository(AbstractRepository):
    """Репозиторий клиентов (CRUD, авторизация, статистика)."""

    # ------------------------------------------------------------------
    # Чтение списков
    # ------------------------------------------------------------------

    def get_all_clients(self) -> list[dict[str, Any]]:
        """Получить список всех активных клиентов."""
        query = f"{_CLIENT_BASE_SELECT} WHERE c.is_active = 1 ORDER BY c.client_id DESC"
        return self.fetch_all(query)

    def get_clients_by_type(self, client_type: str) -> list[dict[str, Any]]:
        """Получить клиентов по типу ('ЮЛ' или 'ФЛ')."""
        query = f"""
            {_CLIENT_BASE_SELECT}
            WHERE c.client_type = %s AND c.is_active = 1
            ORDER BY name
        """
        return self.fetch_all(query, (client_type,))

    def get_client_by_id(self, client_id: int) -> dict[str, Any] | None:
        """Получить клиента по ID."""
        query = f"{_CLIENT_BASE_SELECT} WHERE c.client_id = %s"
        return self.fetch_one(query, (client_id,))

    def get_client_details(self, client_id: int) -> dict[str, Any] | None:
        """Получить детальную информацию о клиенте (включая все поля ЮЛ/ФЛ)."""
        query = f"{_CLIENT_DETAILS_SELECT} WHERE c.client_id = %s"
        return self.fetch_one(query, (client_id,))

    # ------------------------------------------------------------------
    # Авторизация клиента
    # ------------------------------------------------------------------

    def get_client_by_login(
        self, login: str, password_hash: str
    ) -> dict[str, Any] | None:
        """Найти клиента по email или телефону и паролю (для авторизации)."""
        query = f"""
            {_CLIENT_BASE_SELECT}
            WHERE (c.email = %s OR c.phone = %s)
              AND c.password_hash = %s
              AND c.is_active = 1
        """
        return self.fetch_one(query, (login, login, password_hash))

    def client_login_exists(
        self, login: str, exclude_id: int | None = None
    ) -> bool:
        """Проверить, существует ли клиент с таким email или телефоном."""
        if exclude_id is not None:
            query = """
                SELECT 1 FROM clients
                WHERE (email = %s OR phone = %s) AND client_id <> %s
                LIMIT 1
            """
            row = self.fetch_one(query, (login, login, exclude_id))
        else:
            query = """
                SELECT 1 FROM clients
                WHERE email = %s OR phone = %s
                LIMIT 1
            """
            row = self.fetch_one(query, (login, login))
        return row is not None

    def set_client_password(
        self, client_id: int, password_hash: str
    ) -> None:
        """Установить пароль клиенту."""
        query = "UPDATE clients SET password_hash = %s WHERE client_id = %s"
        self.update(query, (password_hash, client_id))

    # ------------------------------------------------------------------
    # Статистика
    # ------------------------------------------------------------------

    def get_clients_stats(self) -> dict[str, Any]:
        """Общая статистика по всем клиентам."""
        total_row = self.fetch_one(
            "SELECT COUNT(*) AS total_clients FROM clients WHERE is_active = 1"
        )
        total = int(total_row["total_clients"]) if total_row else 0

        with_orders_row = self.fetch_one("""
            SELECT COUNT(DISTINCT o.client_id) AS clients_with_orders
            FROM orders o
            JOIN clients c ON c.client_id = o.client_id
            WHERE c.is_active = 1
        """)
        with_orders = int(with_orders_row["clients_with_orders"]) if with_orders_row else 0

        return {
            "total_clients": total,
            "active_clients": total,
            "clients_with_orders": with_orders,
        }

    def get_client_stats(self, client_id: int) -> dict[str, Any]:
        """Статистика для конкретного клиента."""
        total_orders_row = self.fetch_one(
            "SELECT COUNT(*) AS total_orders FROM orders WHERE client_id = %s",
            (client_id,),
        )
        total_orders = int(total_orders_row["total_orders"]) if total_orders_row else 0

        active_orders_row = self.fetch_one("""
            SELECT COUNT(*) AS active_orders FROM orders
            WHERE client_id = %s
              AND status NOT IN ('Завершён', 'В архиве')
        """, (client_id,))
        active_orders = int(active_orders_row["active_orders"]) if active_orders_row else 0

        completed_orders_row = self.fetch_one("""
            SELECT COUNT(*) AS completed_orders FROM orders
            WHERE client_id = %s AND status = 'Завершён'
        """, (client_id,))
        completed_orders = int(completed_orders_row["completed_orders"]) if completed_orders_row else 0

        total_reports_row = self.fetch_one("""
            SELECT COUNT(*) AS total_reports
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            WHERE o.client_id = %s
        """, (client_id,))
        total_reports = int(total_reports_row["total_reports"]) if total_reports_row else 0

        return {
            "total_orders": total_orders,
            "active_orders": active_orders,
            "completed_orders": completed_orders,
            "total_reports": total_reports,
        }

    def get_clients_orders_count(self) -> dict[int, int]:
        """Количество заказов по каждому клиенту (client_id -> count)."""
        rows = self.fetch_all("SELECT client_id, COUNT(*) AS cnt FROM orders GROUP BY client_id")
        return {int(row["client_id"]): int(row["cnt"]) for row in rows}

    # ------------------------------------------------------------------
    # Заказы, отчёты, результаты клиента
    # ------------------------------------------------------------------

    def get_client_orders(
        self, client_id: int, limit: int | None = None
    ) -> list[dict[str, Any]]:
        """Получить заказы клиента."""
        query = """
            SELECT o.order_id, o.vessel_code, o.order_date, o.status, o.total_price,
                   e.full_name AS employee_name
            FROM orders o
            LEFT JOIN employees e ON e.employee_id = o.employee_id
            WHERE o.client_id = %s
            ORDER BY o.order_date DESC
        """
        if limit is not None:
            query += f" LIMIT {int(limit)}"
        return self.fetch_all(query, (client_id,))

    def get_client_reports(self, client_id: int) -> list[dict[str, Any]]:
        """Получить все отчёты клиента."""
        query = """
            SELECT r.report_id, r.report_date, r.file_path,
                   o.vessel_code, o.order_id
            FROM reports r
            JOIN orders o ON o.order_id = r.order_id
            WHERE o.client_id = %s
            ORDER BY r.report_date DESC
        """
        return self.fetch_all(query, (client_id,))

    def get_client_results(self, client_id: int) -> list[dict[str, Any]]:
        """Получить результаты исследований по всем заказам клиента."""
        query = """
            SELECT rr.research_id, rr.result_value, rr.conclusion, rr.result_date,
                   o.order_id, o.vessel_code, o.order_date,
                   s.service_name
            FROM research_results rr
            JOIN order_services os ON os.order_service_id = rr.order_service_id
            JOIN orders o ON o.order_id = os.order_id
            JOIN services s ON s.service_id = os.service_id
            WHERE o.client_id = %s
            ORDER BY o.order_date DESC, s.service_name
        """
        return self.fetch_all(query, (client_id,))

    # ------------------------------------------------------------------
    # Создание / обновление
    # ------------------------------------------------------------------

    def create_client(
        self,
        client_type: str,
        name: str,
        phone: str = "",
        email: str = "",
        password_hash: str = "",
        **kwargs: Any,
    ) -> int:
        """Создать нового клиента. Возвращает client_id."""
        with self.db.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO clients (client_type, password_hash, phone, email, is_active)
                    VALUES (%s, %s, %s, %s, 1)
                    """,
                    (client_type, password_hash or None, phone, email),
                )
                client_id = int(cur.lastrowid)

                if client_type == "ЮЛ":
                    cur.execute(
                        """
                        INSERT INTO legal_entities
                            (client_id, company_name, address, inn, kpp,
                             checking_account, bik, director_name, contact_person)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        """,
                        (
                            client_id,
                            name,
                            kwargs.get("address", ""),
                            kwargs.get("inn", ""),
                            kwargs.get("kpp", ""),
                            kwargs.get("bank_account", ""),
                            kwargs.get("bik", ""),
                            kwargs.get("director_name", ""),
                            kwargs.get("contact_person", ""),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO individuals
                            (client_id, full_name, birth_date,
                             passport_series, passport_number)
                        VALUES (%s, %s, %s, %s, %s)
                        """,
                        (
                            client_id,
                            name,
                            kwargs.get("birth_date"),
                            kwargs.get("passport_series", ""),
                            kwargs.get("passport_number", ""),
                        ),
                    )
        return client_id

    def update_client(
        self,
        client_id: int,
        client_type: str,
        name: str,
        phone: str = "",
        email: str = "",
        password_hash: str = "",
        **kwargs: Any,
    ) -> None:
        """Обновить данные клиента."""
        with self.db.transaction() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE clients
                    SET client_type = %s,
                        password_hash = COALESCE(%s, password_hash),
                        phone = %s, email = %s
                    WHERE client_id = %s
                    """,
                    (client_type, password_hash or None, phone, email, client_id),
                )

                if client_type == "ЮЛ":
                    cur.execute(
                        """
                        INSERT INTO legal_entities
                            (client_id, company_name, address, inn, kpp,
                             checking_account, bik, director_name, contact_person)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            company_name = VALUES(company_name),
                            address = VALUES(address),
                            inn = VALUES(inn),
                            kpp = VALUES(kpp),
                            checking_account = VALUES(checking_account),
                            bik = VALUES(bik),
                            director_name = VALUES(director_name),
                            contact_person = VALUES(contact_person)
                        """,
                        (
                            client_id,
                            name,
                            kwargs.get("address", ""),
                            kwargs.get("inn", ""),
                            kwargs.get("kpp", ""),
                            kwargs.get("bank_account", ""),
                            kwargs.get("bik", ""),
                            kwargs.get("director_name", ""),
                            kwargs.get("contact_person", ""),
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO individuals
                            (client_id, full_name, birth_date,
                             passport_series, passport_number)
                        VALUES (%s, %s, %s, %s, %s)
                        ON DUPLICATE KEY UPDATE
                            full_name = VALUES(full_name),
                            birth_date = VALUES(birth_date),
                            passport_series = VALUES(passport_series),
                            passport_number = VALUES(passport_number)
                        """,
                        (
                            client_id,
                            name,
                            kwargs.get("birth_date"),
                            kwargs.get("passport_series", ""),
                            kwargs.get("passport_number", ""),
                        ),
                    )

    # ------------------------------------------------------------------
    # Алиасы для обратной совместимости
    # ------------------------------------------------------------------

    def add_client(self, data: dict[str, Any]) -> int:
        """Обёртка, принимающая словарь (для client_dialog.py)."""
        return self.create_client(
            client_type=data.get("client_type", "ЮЛ"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            **{
                k: v
                for k, v in data.items()
                if k not in ("client_type", "name", "phone", "email", "password_hash")
            },
        )

    def update_client_data(self, data: dict[str, Any]) -> None:
        """Обёртка, принимающая словарь (для client_dialog.py)."""
        self.update_client(
            client_id=data.get("client_id"),
            client_type=data.get("client_type", "ЮЛ"),
            name=data.get("name", ""),
            phone=data.get("phone", ""),
            email=data.get("email", ""),
            password_hash=data.get("password_hash", ""),
            **{
                k: v
                for k, v in data.items()
                if k not in ("client_id", "client_type", "name", "phone", "email", "password_hash")
            },
        )

    def get_client_info(self, client_id: int) -> dict[str, Any] | None:
        """Алиас для get_client_by_id (для client_window.py)."""
        return self.get_client_by_id(client_id)


__all__ = ["ClientRepository"]
