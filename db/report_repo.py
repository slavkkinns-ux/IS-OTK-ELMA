"""Репозиторий отчётов и исследований."""
from db.connection import get_connection


def get_research_queue() -> list[dict]:
    """Очередь исследований."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT os.order_service_id, o.order_id, o.vessel_code,
                       s.service_name,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       rr.result_value
                FROM order_services os
                JOIN orders o ON o.order_id = os.order_id
                JOIN services s ON s.service_id = os.service_id
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type='ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type='ФЛ'
                LEFT JOIN research_results rr ON rr.order_service_id = os.order_service_id
                WHERE o.status NOT IN ('Завершён', 'В архиве')
                ORDER BY o.order_date DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_report_research(order_id: int) -> list[dict]:
    """Исследования по конкретному заказу."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.service_name, rr.result_value, rr.conclusion
                FROM order_services os
                JOIN services s ON s.service_id = os.service_id
                LEFT JOIN research_results rr ON rr.order_service_id = os.order_service_id
                WHERE os.order_id = %s
                ORDER BY s.service_name
            """, (order_id,))
            return cur.fetchall()
    finally:
        conn.close()


def get_recent_reports(limit: int = 10) -> list[dict]:
    """Последние отчёты."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.report_id, o.vessel_code, r.report_date, e.full_name AS employee_name
                FROM reports r
                JOIN orders o ON o.order_id = r.order_id
                JOIN employees e ON e.employee_id = r.employee_id
                ORDER BY r.report_date DESC
                LIMIT %s
            """, (limit,))
            return cur.fetchall()
    finally:
        conn.close()