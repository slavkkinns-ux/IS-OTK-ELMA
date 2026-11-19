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

def save_research_result(order_service_id: int, employee_id: int, 
                         result_value: str, conclusion: str, result_date) -> int:
    """Сохранить или обновить результат исследования. Возвращает research_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            # Проверяем, есть ли уже результат
            cur.execute("""
                SELECT research_id FROM research_results 
                WHERE order_service_id = %s
            """, (order_service_id,))
            existing = cur.fetchone()
            
            if existing:
                # Обновляем существующий
                cur.execute("""
                    UPDATE research_results
                    SET result_value = %s, conclusion = %s, 
                        result_date = %s, employee_id = %s
                    WHERE order_service_id = %s
                """, (result_value, conclusion, result_date, employee_id, order_service_id))
                research_id = existing['research_id']
            else:
                # Создаём новый
                cur.execute("""
                    INSERT INTO research_results 
                    (order_service_id, result_value, conclusion, result_date, employee_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_service_id, result_value, conclusion, result_date, employee_id))
                research_id = cur.lastrowid
            
            conn.commit()
            return research_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_research_result(order_service_id: int) -> dict | None:
    """Получить результат исследования по order_service_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT research_id, result_value, conclusion, result_date, employee_id
                FROM research_results
                WHERE order_service_id = %s
            """, (order_service_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_all_employees() -> list[dict]:
    """Получить список активных сотрудников."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT employee_id, full_name, role
                FROM employees
                WHERE is_active = 1
                ORDER BY full_name
            """)
            return cur.fetchall()
    finally:
        conn.close()