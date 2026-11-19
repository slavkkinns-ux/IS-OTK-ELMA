"""Репозиторий услуг."""
from db.connection import get_connection


def get_all_services(include_inactive: bool = False) -> list[dict]:
    """Получить все услуги. include_inactive — показывать также отключённые."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if include_inactive:
                cur.execute("""
                    SELECT service_id, service_name, price, is_active
                    FROM services
                    ORDER BY service_name
                """)
            else:
                cur.execute("""
                    SELECT service_id, service_name, price, is_active
                    FROM services
                    WHERE is_active = 1
                    ORDER BY service_name
                """)
            return cur.fetchall()
    finally:
        conn.close()


def add_service(service_name: str, price: float) -> int:
    """Добавить новую услугу. Возвращает service_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO services (service_name, price, is_active)
                VALUES (%s, %s, 1)
            """, (service_name, price))
            service_id = cur.lastrowid
            conn.commit()
            return service_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_service(service_id: int, service_name: str, price: float, is_active: int = 1):
    """Обновить услугу."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE services
                SET service_name = %s, price = %s, is_active = %s
                WHERE service_id = %s
            """, (service_name, price, is_active, service_id))
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_service(service_id: int, soft: bool = True):
    """Удалить услугу. soft=True — пометить неактивной, False — физически удалить."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if soft:
                cur.execute("""
                    UPDATE services SET is_active = 0 WHERE service_id = %s
                """, (service_id,))
            else:
                cur.execute("DELETE FROM services WHERE service_id = %s", (service_id,))
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def service_name_exists(service_name: str, exclude_id: int = None) -> bool:
    """Проверить, существует ли услуга с таким именем."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute("""
                    SELECT 1 FROM services
                    WHERE service_name = %s AND service_id <> %s
                    LIMIT 1
                """, (service_name, exclude_id))
            else:
                cur.execute("""
                    SELECT 1 FROM services
                    WHERE service_name = %s
                    LIMIT 1
                """, (service_name,))
            return cur.fetchone() is not None
    finally:
        conn.close()

def is_service_used(service_id: int) -> bool:
    """Проверить, используется ли услуга в заказах."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 1 FROM order_services WHERE service_id = %s LIMIT 1
            """, (service_id,))
            return cur.fetchone() is not None
    finally:
        conn.close()