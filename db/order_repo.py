"""Репозиторий заказов. MySQL + DictCursor."""
from db.connection import get_connection


def get_active_services() -> list[dict]:
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
    """Полная карточка заказа. Возвращает также client_type."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       c.client_id, c.client_type,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type='ФЛ'
                JOIN employees e ON e.employee_id = o.employee_id
                WHERE o.order_id = %s
            """, (order_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_order_services(order_id: int):
    """Получить услуги заказа с реальными ценами из price_at_order."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT os.order_service_id, os.service_id, s.service_name,
                       os.price_at_order AS price
                FROM order_services os
                JOIN services s ON s.service_id = os.service_id
                WHERE os.order_id = %s
                ORDER BY os.order_service_id
            """, (order_id,))
            return cur.fetchall()
    finally:
        conn.close()


def get_next_vessel_code() -> str:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT vessel_code FROM orders ORDER BY order_id DESC")
            rows = cur.fetchall()
            for row in rows:
                code = row['vessel_code']
                if '-' in code:
                    try:
                        prefix, num = code.rsplit('-', 1)
                        next_num = int(num) + 1
                        return f"{prefix}-{next_num:04d}"
                    except ValueError:
                        continue
            return "С-0001"
    finally:
        conn.close()


def vessel_code_exists(code: str, exclude_archived: bool = True,
                       exclude_order_id: int | None = None) -> bool:
    """Проверка дубликата."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = "SELECT 1 FROM orders WHERE vessel_code = %s "
            params = [code]
            if exclude_archived:
                sql += " AND status != 'В архиве' "
            if exclude_order_id is not None:
                sql += " AND order_id <> %s "
                params.append(exclude_order_id)
            sql += " LIMIT 1 "
            cur.execute(sql, tuple(params))
            return cur.fetchone() is not None
    finally:
        conn.close()


def create_order(vessel_code: str, client_id: int, employee_id: int,
                 service_ids: list[int], total_price: float) -> int:
    """Создать заказ. Сохраняет РЕАЛЬНУЮ цену каждой услуги в price_at_order."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO orders (vessel_code, client_id, employee_id, order_date, status)
                VALUES (%s, %s, %s, CURRENT_TIMESTAMP, 'Новый')
            """, (vessel_code, client_id, employee_id))
            order_id = cur.lastrowid

            # Берём реальную цену каждой услуги из справочника services
            for sid in service_ids:
                cur.execute("SELECT price FROM services WHERE service_id = %s", (sid,))
                row = cur.fetchone()
                price = float(row['price']) if row else 0
                cur.execute("""
                    INSERT INTO order_services (order_id, service_id, price_at_order)
                    VALUES (%s, %s, %s)
                """, (order_id, sid, price))
            conn.commit()
            return order_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_order(order_id: int, vessel_code: str, client_id: int,
                 employee_id: int, service_ids: list[int], total_price: float):
    """Обновление заказа: шапка + пересоздание услуг с реальными ценами."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE orders
                SET vessel_code = %s,
                    client_id   = %s,
                    employee_id = %s
                WHERE order_id = %s
            """, (vessel_code, client_id, employee_id, order_id))
            cur.execute("DELETE FROM order_services WHERE order_id = %s", (order_id,))

            # Берём реальную цену каждой услуги из справочника services
            for sid in service_ids:
                cur.execute("SELECT price FROM services WHERE service_id = %s", (sid,))
                row = cur.fetchone()
                price = float(row['price']) if row else 0
                cur.execute("""
                    INSERT INTO order_services (order_id, service_id, price_at_order)
                    VALUES (%s, %s, %s)
                """, (order_id, sid, price))
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def search_orders(query: str):
    conn = get_connection()
    try:
        like = f"%{query}%"
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type='ФЛ'
                JOIN employees e ON e.employee_id = o.employee_id
                WHERE o.vessel_code LIKE %s
                   OR le.company_name LIKE %s
                   OR i.full_name LIKE %s
                   OR o.status LIKE %s
                ORDER BY o.order_date DESC
            """, (like, like, like, like))
            return cur.fetchall()
    finally:
        conn.close()


def get_all_orders() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type='ФЛ'
                JOIN employees e ON e.employee_id = o.employee_id
                ORDER BY o.order_date DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_orders_stats() -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total,
                       SUM(CASE WHEN status = 'В работе' THEN 1 ELSE 0 END) AS in_progress,
                       SUM(CASE WHEN status = 'Ожидает контроля' THEN 1 ELSE 0 END) AS pending,
                       SUM(CASE WHEN status = 'Завершён' THEN 1 ELSE 0 END) AS completed
                FROM orders
            """)
            row = cur.fetchone()
            return {
                'total': row['total'] or 0,
                'in_progress': row['in_progress'] or 0,
                'pending': row['pending'] or 0,
                'completed': row['completed'] or 0
            }
    finally:
        conn.close()


def get_home_stats() -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total_orders,
                       SUM(CASE WHEN status NOT IN ('Завершён', 'В архиве') THEN 1 ELSE 0 END) AS active_orders,
                       (SELECT COUNT(*) FROM clients WHERE is_active = 1) AS total_clients,
                       SUM(CASE WHEN status = 'Ожидает контроля' THEN 1 ELSE 0 END) AS pending_checks
                FROM orders
            """)
            row = cur.fetchone()
            return {
                'total_orders': row['total_orders'] or 0,
                'active_orders': row['active_orders'] or 0,
                'total_clients': row['total_clients'] or 0,
                'pending_checks': row['pending_checks'] or 0
            }
    finally:
        conn.close()


def get_recent_orders(limit: int = 5) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT o.order_id, o.vessel_code, o.order_date, o.status,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name
                FROM orders o
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type='ФЛ'
                ORDER BY o.order_date DESC LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()