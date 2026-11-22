"""Репозиторий отчётов и исследований. MySQL + DictCursor."""
from db.connection import get_connection


# =============================================================================
# ОЧЕРЕДЬ ИССЛЕДОВАНИЙ
# =============================================================================

def get_research_queue() -> list[dict]:
    """Очередь исследований (все услуги активных заказов)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT os.order_service_id,
                       o.order_id,
                       o.vessel_code,
                       s.service_name,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       rr.result_value
                FROM order_services os
                JOIN orders o ON o.order_id = os.order_id
                JOIN services s ON s.service_id = os.service_id
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le
                       ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i
                       ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                LEFT JOIN research_results rr
                       ON rr.order_service_id = os.order_service_id
                WHERE o.status NOT IN ('Завершён', 'В архиве')
                ORDER BY o.order_date DESC, o.order_id DESC
            """)
            return cur.fetchall()
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


def save_research_result(order_service_id: int, employee_id: int,
                         result_value: str, conclusion: str, result_date) -> int:
    """Сохранить или обновить результат исследования. Возвращает research_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT research_id FROM research_results
                WHERE order_service_id = %s
            """, (order_service_id,))
            existing = cur.fetchone()

            if existing:
                cur.execute("""
                    UPDATE research_results
                    SET result_value = %s,
                        conclusion   = %s,
                        result_date  = %s,
                        employee_id  = %s
                    WHERE order_service_id = %s
                """, (result_value, conclusion, result_date, employee_id, order_service_id))
                research_id = existing['research_id']
            else:
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


def get_all_employees() -> list[dict]:
    """Список активных сотрудников."""
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


# =============================================================================
# ИССЛЕДОВАНИЯ ПО ЗАКАЗУ (для вкладки «Отчёты»)
# =============================================================================

def get_report_research(order_id: int) -> list[dict]:
    """Исследования по конкретному заказу (для таблицы в отчёте)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT s.service_name, rr.result_value, rr.conclusion
                FROM order_services os
                JOIN services s ON s.service_id = os.service_id
                LEFT JOIN research_results rr
                       ON rr.order_service_id = os.order_service_id
                WHERE os.order_id = %s
                ORDER BY s.service_name
            """, (order_id,))
            return cur.fetchall()
    finally:
        conn.close()


# =============================================================================
# ОТЧЁТЫ
# =============================================================================

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


def get_report(report_id: int) -> dict | None:
    """Получить данные отчёта по ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.report_id, r.order_id, r.employee_id, r.report_date, r.file_path,
                       o.vessel_code,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM reports r
                JOIN orders o ON o.order_id = r.order_id
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le
                       ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i
                       ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                JOIN employees e ON e.employee_id = r.employee_id
                WHERE r.report_id = %s
            """, (report_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_report_by_order(order_id: int) -> dict | None:
    """Получить последний отчёт по заказу (для проверки дубликата)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.report_id, r.order_id, r.employee_id, r.report_date, r.file_path,
                       o.vessel_code,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS client_name,
                       e.full_name AS employee_name
                FROM reports r
                JOIN orders o ON o.order_id = r.order_id
                JOIN clients c ON c.client_id = o.client_id
                LEFT JOIN legal_entities le
                       ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i
                       ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                JOIN employees e ON e.employee_id = r.employee_id
                WHERE r.order_id = %s
                ORDER BY r.report_date DESC
                LIMIT 1
            """, (order_id,))
            return cur.fetchone()
    finally:
        conn.close()


def create_report(order_id: int, employee_id: int, file_path: str) -> int:
    """Создать запись отчёта в БД. Возвращает report_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO reports (order_id, employee_id, file_path)
                VALUES (%s, %s, %s)
            """, (order_id, employee_id, file_path))
            report_id = cur.lastrowid
            conn.commit()
            return report_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_next_report_number() -> int:
    """Получить следующий номер отчёта."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT MAX(report_id) FROM reports")
            result = cur.fetchone()
            max_id = result[0] if result and result[0] else 0
            return max_id + 1
    finally:
        conn.close()

def get_report_by_path(file_path: str) -> dict | None:
    """Найти отчёт по пути к файлу."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.report_id, r.order_id, r.report_date, r.file_path,
                       o.vessel_code, e.full_name as employee_name
                FROM reports r
                JOIN orders o ON o.order_id = r.order_id
                JOIN employees e ON e.employee_id = r.employee_id
                WHERE r.file_path = %s
            """, (file_path,))
            return cur.fetchone()
    finally:
        conn.close()

def delete_report(report_id: int):
    """Удалить отчёт из базы данных."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM reports WHERE report_id = %s", (report_id,))
            conn.commit()
    finally:
        conn.close()

def update_report_path(report_id: int, file_path: str):
    """Обновить путь к файлу отчёта."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE reports 
                SET file_path = %s 
                WHERE report_id = %s
            """, (file_path, report_id))
            conn.commit()
    finally:
        conn.close()

