"""Репозиторий заказов — доступ к данным о заказах и связанных услугах."""

from __future__ import annotations

from typing import Any

from db.repositories.base import AbstractRepository

# Общий SQL для выборки заказа с данными клиента и сотрудника.
_ORDER_WITH_CLIENT_SELECT = """
    SELECT
        o.order_id, o.vessel_code, o.order_date, o.status, o.total_price,
        c.client_id, c.client_type,
        CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
             ELSE i.full_name END AS client_name,
        e.full_name AS employee_name
    FROM orders o
    JOIN clients c ON c.client_id = o.client_id
    LEFT JOIN legal_entities le
        ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
    LEFT JOIN individuals i
        ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
    JOIN employees e ON e.employee_id = o.employee_id
"""


class OrderRepository(AbstractRepository):
    """Репозиторий заказов."""

    # ------------------------------------------------------------------
    # Чтение
    # ------------------------------------------------------------------

    def get_active_services(self) -> list[dict[str, Any]]:
        """Получить список активных услуг (для выбора при создании заказа)."""
        query = """
            SELECT service_id, service_name, price
            FROM services
            WHERE is_active = 1
            ORDER BY service_name
        """
        return self.fetch_all(query)

    def get_order(self, order_id: int) -> dict[str, Any] | None:
        """Получить полную карточку заказа с данными клиента и сотрудника."""
        query = f"{_ORDER_WITH_CLIENT_SELECT} WHERE o.order_id = %s"
        return self.fetch_one(query, (order_id,))

    def get_order_services(self, order_id: int) -> list[dict[str, Any]]:
        """Получить услуги заказа с ценами на момент заказа."""
        query = """
            SELECT
                os.order_service_id,
                os.service_id,
                s.service_name,
                os.price_at_order AS price
            FROM order_services os
            JOIN services s ON s.service_id = os.service_id
            WHERE os.order_id = %s
            ORDER BY os.order_service_id
        """
        return self.fetch_all(query, (order_id,))

    def get_next_vessel_code(self) -> str:
        """Сгенерировать следующий код лабораторного сосуда (С-0001, С-0002, ...)."""
        rows = self.fetch_all("SELECT vessel_code FROM orders ORDER BY order_id DESC")
        for row in rows:
            code = row["vessel_code"]
            if "-" in code:
                try:
                    prefix, num = code.rsplit("-", 1)
                    next_num = int(num) + 1
                    return f"{prefix}-{next_num:04d}"
                except ValueError:
                    continue
        return "С-0001"

    def vessel_code_exists(
        self,
        code: str,
        exclude_archived: bool = True,
        exclude_order_id: int | None = None,
    ) -> bool:
        """Проверить, существует ли уже заказ с таким кодом сосуда."""
        sql = "SELECT 1 FROM orders WHERE vessel_code = %s"
        params: list[Any] = [code]
        if exclude_archived:
            sql += " AND status != 'В архиве'"
        if exclude_order_id is not None:
            sql += " AND order_id <> %s"
            params.append(exclude_order_id)
        sql += " LIMIT 1"
        row = self.fetch_one(sql, tuple(params))
        return row is not None

    def search_orders(self, query: str) -> list[dict[str, Any]]:
        """Поиск заказов по коду сосуда, клиенту, статусу."""
        like = f"%{query}%"
        sql = f"""
            {_ORDER_WITH_CLIENT_SELECT}
            WHERE o.vessel_code LIKE %s
               OR le.company_name LIKE %s
               OR i.full_name LIKE %s
               OR o.status LIKE %s
            ORDER BY o.order_date DESC
        """
        return self.fetch_all(sql, (like, like, like, like))

    def get_all_orders(self) -> list[dict[str, Any]]:
        """Получить все заказы."""
        sql = f"{_ORDER_WITH_CLIENT_SELECT} ORDER BY o.order_date DESC"
        return self.fetch_all(sql)

    def get_orders_stats(self) -> dict[str, Any]:
        """Статистика заказов по статусам."""
        row = self.fetch_one("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status = 'В работе' THEN 1 ELSE 0 END) AS in_progress,
                SUM(CASE WHEN status = 'Ожидает контроля' THEN 1 ELSE 0 END) AS pending,
                SUM(CASE WHEN status = 'Завершён' THEN 1 ELSE 0 END) AS completed
            FROM orders
        """)
        if not row:
            return {"total": 0, "in_progress": 0, "pending": 0, "completed": 0}
        return {
            "total": int(row["total"] or 0),
            "in_progress": int(row["in_progress"] or 0),
            "pending": int(row["pending"] or 0),
            "completed": int(row["completed"] or 0),
        }

    def get_home_stats(self) -> dict[str, Any]:
        """Статистика для главной страницы."""
        row = self.fetch_one("""
            SELECT
                COUNT(*) AS total_orders,
                SUM(CASE WHEN status NOT IN ('Завершён', 'В архиве') THEN 1 ELSE 0 END) AS active_orders,
                (SELECT COUNT(*) FROM clients WHERE is_active = 1) AS total_clients,
                SUM(CASE WHEN status = 'Ожидает контроля' THEN 1 ELSE 0 END) AS pending_checks
            FROM orders
        """)
        if not row:
            return {
                "total_orders": 0,
                "active_orders": 0,
                "total_clients": 0,
                "pending_checks": 0,
            }
        return {
            "total_orders": int(row["total_orders"] or 0),
            "active_orders": int(row["active_orders"] or 0),
            "total_clients": int(row["total_clients"] or 0),
            "pending_checks": int(row["pending_checks"] or 0),
        }

    def get_recent_orders(self, limit: int = 5) -> list[dict[str, Any]]:
        """Получить последние заказы."""
        sql = f"""
            {_ORDER_WITH_CLIENT_SELECT}
            ORDER BY o.order_date DESC
            LIMIT %s
        """
        return self.fetch_all(sql, (limit,))

    # ------------------------------------------------------------------
    # Создание / обновление
    # ------------------------------------------------------------------

    def create_order(
        self,
        vessel_code: str,
        client_id: int,
        employee_id: int,
        service_ids: list[int],
        total_price: float,
    ) -> int:
        """Создать заказ с услугами. Сохраняет реальную цену каждой услуги."""
        with self.db.transaction() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    INSERT INTO orders (vessel_code, client_id, employee_id, order_date, status)
                    VALUES (%s, %s, %s, CURRENT_TIMESTAMP, 'Новый')
                    """,
                (vessel_code, client_id, employee_id),
            )
            order_id = int(cur.lastrowid)

            # Берём реальную цену каждой услуги из справочника services
            for sid in service_ids:
                cur.execute("SELECT price FROM services WHERE service_id = %s", (sid,))
                row = cur.fetchone()
                price = float(row["price"]) if row else 0.0
                cur.execute(
                    """
                        INSERT INTO order_services (order_id, service_id, price_at_order)
                        VALUES (%s, %s, %s)
                        """,
                    (order_id, sid, price),
                )
        return order_id

    def update_order(
        self,
        order_id: int,
        vessel_code: str,
        client_id: int,
        employee_id: int,
        service_ids: list[int],
        total_price: float,
    ) -> None:
        """Обновить заказ: шапка + пересоздание услуг с реальными ценами."""
        with self.db.transaction() as conn, conn.cursor() as cur:
            cur.execute(
                """
                    UPDATE orders
                    SET vessel_code = %s,
                        client_id   = %s,
                        employee_id = %s
                    WHERE order_id = %s
                    """,
                (vessel_code, client_id, employee_id, order_id),
            )
            cur.execute(
                "DELETE FROM order_services WHERE order_id = %s",
                (order_id,),
            )
            for sid in service_ids:
                cur.execute(
                    "SELECT price FROM services WHERE service_id = %s",
                    (sid,),
                )
                row = cur.fetchone()
                price = float(row["price"]) if row else 0.0
                cur.execute(
                    """
                        INSERT INTO order_services (order_id, service_id, price_at_order)
                        VALUES (%s, %s, %s)
                        """,
                    (order_id, sid, price),
                )


__all__ = ["OrderRepository"]
