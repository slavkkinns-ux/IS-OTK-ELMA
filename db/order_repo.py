from db.connection import get_connection   # ваш модуль подключения


def get_active_services():
    """Список активных услуг (справочник)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT service_id, service_name, price "
                "FROM services WHERE is_active = 1 ORDER BY service_name"
            )
            return cur.fetchall()
    finally:
        conn.close()


def get_order(order_id: int):
    """Полная карточка заказа (один заказ с именем клиента и сотрудника)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       c.client_id,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals    i  ON i.client_id  = c.client_id AND c.client_type='ФЛ'
                JOIN employees e ON e.employee_id = o.employee_id
                WHERE o.order_id = %s
                """,
                (order_id,),
            )
            return cur.fetchone()
    finally:
        conn.close()


def get_order_services(order_id: int):
    """Услуги заказа (для редактирования)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT os.order_service_id, os.service_id, s.service_name,
                       os.price_at_order AS price
                FROM order_services os
                JOIN services s ON s.service_id = os.service_id
                WHERE os.order_id = %s
                ORDER BY os.order_service_id
                """,
                (order_id,),
            )
            return cur.fetchall()
    finally:
        conn.close()


def create_order(payload: dict) -> int:
    """Создание заказа + привязка услуг. Возвращает order_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO orders (vessel_code, client_id, employee_id, status)
                VALUES (%s, %s, %s, %s)
                """,
                (payload["vessel_code"], payload["client_id"],
                 payload["employee_id"], payload["status"]),
            )
            order_id = cur.lastrowid

            for s in payload["services"]:
                cur.execute(
                    """
                    INSERT INTO order_services (order_id, service_id, price_at_order)
                    VALUES (%s, %s, %s)
                    """,
                    (order_id, s["service_id"], s["price"]),
                )
        conn.commit()
        return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_order(order_id: int, payload: dict):
    """Обновление заказа: шапка + пересоздание услуг."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE orders
                SET vessel_code = %s,
                    client_id   = %s,
                    status      = %s
                WHERE order_id = %s
                """,
                (payload["vessel_code"], payload["client_id"],
                 payload["status"], order_id),
            )
            # Удаляем старые услуги и вставляем новые
            cur.execute("DELETE FROM order_services WHERE order_id = %s", (order_id,))
            for s in payload["services"]:
                cur.execute(
                    """
                    INSERT INTO order_services (order_id, service_id, price_at_order)
                    VALUES (%s, %s, %s)
                    """,
                    (order_id, s["service_id"], s["price"]),
                )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def search_orders(query: str):
    """Поиск заказов по коду судна / клиенту / статусу."""
    conn = get_connection()
    try:
        like = f"%{query}%"
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals    i  ON i.client_id  = c.client_id AND c.client_type='ФЛ'
                JOIN employees e ON e.employee_id = o.employee_id
                WHERE o.vessel_code LIKE %s
                   OR (le.company_name LIKE %s)
                   OR (i.full_name    LIKE %s)
                   OR o.status        LIKE %s
                ORDER BY o.order_date DESC
                """,
                (like, like, like, like),
            )
            return cur.fetchall()
    finally:
        conn.close()