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


# def get_all_employees() -> list[dict]:
#     """Список активных сотрудников."""
#     conn = get_connection()
#     try:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT employee_id, full_name, role
#                 FROM employees
#                 WHERE is_active = 1
#                 ORDER BY full_name
#             """)
#             return cur.fetchall()
#     finally:
#         conn.close()


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

# =============================================================================
# Employee Repository
# =============================================================================

def get_all_employees(role_filter=None, active_only=False, search_query=None) -> list[dict]:
    """Получить список сотрудников с фильтрацией."""
    conn = get_connection()
    try:
        query = """
            SELECT e.employee_id, e.full_name, e.login, e.role, e.is_active,
                   e.email, e.phone, e.last_login, e.created_at,
                   e.created_by,
                   (SELECT COUNT(*) FROM research_results rr 
                    WHERE rr.employee_id = e.employee_id) as research_count,
                   (SELECT COUNT(*) FROM reports r WHERE r.employee_id = e.employee_id) as report_count
            FROM employees e
            WHERE 1=1
        """
        params = []
        
        if role_filter:
            query += " AND e.role = %s"
            params.append(role_filter)
        
        if active_only:
            query += " AND e.is_active = 1"
        
        if search_query:
            query += " AND (e.full_name LIKE %s OR e.login LIKE %s)"
            params.extend([f"%{search_query}%", f"%{search_query}%"])
        
        query += " ORDER BY e.full_name"
        
        with conn.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()
    finally:
        conn.close()


def get_employee(employee_id: int) -> dict | None:
    """Получить сотрудника по ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT e.employee_id, e.full_name, e.login, e.role, e.is_active,
                       e.must_change_password, e.email, e.phone, e.last_login, e.created_at,
                       e.created_by
                FROM employees e
                WHERE e.employee_id = %s
            """, (employee_id,))
            return cur.fetchone()
    finally:
        conn.close()


def create_employee(full_name: str, login: str, password: str, role: str, 
                   is_active: bool = True, email: str = None, phone: str = None,
                   created_by: int = None) -> int:
    """Создать нового сотрудника. Возвращает employee_id."""
    import hashlib
    from datetime import datetime
    
    conn = get_connection()
    try:
        # Хешируем пароль
        password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
        
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO employees (full_name, login, password_hash, role, is_active,
                                      must_change_password, email, phone, created_at, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), %s)
            """, (full_name, login, password_hash, role, 1 if is_active else 0,
                  1, email, phone, created_by))  # must_change_password = 1 при создании
            conn.commit()
            return cur.lastrowid
    finally:
        conn.close()


def update_employee(employee_id: int, full_name: str = None, login: str = None,
                   role: str = None, is_active: bool = None, email: str = None,
                   phone: str = None) -> bool:
    """Обновить данные сотрудника."""
    conn = get_connection()
    try:
        updates = []
        params = []
        
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
        
        with conn.cursor() as cur:
            cur.execute(query, params)
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


def reset_password(employee_id: int, new_password: str = "123456") -> bool:
    """Сбросить пароль сотрудника."""
    import hashlib
    
    conn = get_connection()
    try:
        password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
        
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE employees 
                SET password_hash = %s, must_change_password = 1
                WHERE employee_id = %s
            """, (password_hash, employee_id))
            conn.commit()
            return cur.rowcount > 0
    finally:
        conn.close()


def get_employee_stats() -> dict:
    """Получить статистику по сотрудникам."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
                    SUM(CASE WHEN role = 'manager' THEN 1 ELSE 0 END) as managers,
                    SUM(CASE WHEN role = 'lab_technician' THEN 1 ELSE 0 END) as lab_technicians,
                    SUM(CASE WHEN role = 'controller' THEN 1 ELSE 0 END) as controllers,
                    SUM(CASE WHEN role = 'admin' THEN 1 ELSE 0 END) as admins
                FROM employees
            """)
            return cur.fetchone()
    finally:
        conn.close()


def check_login_exists(login: str, exclude_employee_id: int = None) -> bool:
    """Проверить, существует ли логин."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_employee_id:
                cur.execute("""
                    SELECT COUNT(*) FROM employees 
                    WHERE login = %s AND employee_id != %s
                """, (login, exclude_employee_id))
            else:
                cur.execute("SELECT COUNT(*) FROM employees WHERE login = %s", (login,))
            result = cur.fetchone()
            return result[0] > 0
    finally:
        conn.close()