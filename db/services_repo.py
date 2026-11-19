"""Репозиторий услуг."""
from db.connection import get_connection


def get_all_services() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT service_id, service_name, price
                FROM services
                WHERE is_active = 1
                ORDER BY service_name
            """)
            return cur.fetchall()
    finally:
        conn.close()