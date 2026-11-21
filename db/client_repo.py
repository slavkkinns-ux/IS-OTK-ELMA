"""Репозиторий клиентов."""
from db.connection import get_connection


# ==================== ОБЩИЕ МЕТОДЫ ====================

def get_all_clients() -> list[dict]:
    """Получить список всех активных клиентов."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.client_id, c.client_type, c.phone, c.email, c.login,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS name,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.director_name
                            ELSE i.full_name END AS contact_person,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.address
                            ELSE CONCAT(i.passport_series, ' ', i.passport_number) END AS details
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.is_active = 1
                ORDER BY c.client_id DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def get_clients_by_type(client_type: str) -> list[dict]:
    """Получить клиентов по типу (ЮЛ или ФЛ)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.client_id,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS name,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.director_name
                            ELSE i.full_name END AS contact_person,
                       c.phone, c.email
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.client_type = %s AND c.is_active = 1
                ORDER BY name
            """, (client_type,))
            return cur.fetchall()
    finally:
        conn.close()


def get_client_by_id(client_id: int) -> dict | None:
    """Получить клиента по ID."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, 
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS name,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.director_name
                            ELSE i.full_name END AS contact_person,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.address
                            ELSE CONCAT(i.passport_series, ' ', i.passport_number) END AS details
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.client_id = %s
            """, (client_id,))
            return cur.fetchone()
    finally:
        conn.close()


def get_client_details(client_id: int) -> dict | None:
    """Получить детали клиента (для просмотра/редактирования)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.*, 
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
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.client_id = %s
            """, (client_id,))
            return cur.fetchone()
    finally:
        conn.close()


# ==================== АВТОРИЗАЦИЯ КЛИЕНТА ====================

def get_client_by_login(login: str, password_hash: str) -> dict | None:
    """Найти клиента по логину и паролю (для авторизации)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.client_id, c.client_type, c.login, c.phone, c.email,
                       CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                            ELSE i.full_name END AS full_name
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.login = %s AND c.password_hash = %s AND c.is_active = 1
            """, (login, password_hash))
            return cur.fetchone()
    finally:
        conn.close()


def client_login_exists(login: str, exclude_id: int = None) -> bool:
    """Проверить, существует ли клиент с таким логином."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if exclude_id:
                cur.execute("""
                    SELECT 1 FROM clients WHERE login = %s AND client_id <> %s LIMIT 1
                """, (login, exclude_id))
            else:
                cur.execute("""
                    SELECT 1 FROM clients WHERE login = %s LIMIT 1
                """, (login,))
            return cur.fetchone() is not None
    finally:
        conn.close()


def set_client_password(client_id: int, password_hash: str):
    """Установить пароль клиенту."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE clients SET password_hash = %s WHERE client_id = %s
            """, (password_hash, client_id))
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== СТАТИСТИКА ====================

def get_clients_stats() -> dict:
    """Общая статистика по всем клиентам (для администратора)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS total_clients FROM clients WHERE is_active = 1")
            total = cur.fetchone()['total_clients']

            cur.execute("""
                SELECT COUNT(DISTINCT o.client_id) AS clients_with_orders
                FROM orders o JOIN clients c ON c.client_id = o.client_id
                WHERE c.is_active = 1
            """)
            with_orders = cur.fetchone()['clients_with_orders']

            return {
                'total_clients': total,
                'active_clients': total,
                'clients_with_orders': with_orders,
            }
    finally:
        conn.close()


def get_client_stats(client_id: int) -> dict:
    """Статистика для конкретного клиента (его заказы, отчёты)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total_orders FROM orders WHERE client_id = %s
            """, (client_id,))
            total_orders = cur.fetchone()['total_orders']

            cur.execute("""
                SELECT COUNT(*) AS active_orders 
                FROM orders 
                WHERE client_id = %s AND status NOT IN ('Завершён', 'В архиве')
            """, (client_id,))
            active_orders = cur.fetchone()['active_orders']

            cur.execute("""
                SELECT COUNT(*) AS completed_orders 
                FROM orders 
                WHERE client_id = %s AND status = 'Завершён'
            """, (client_id,))
            completed_orders = cur.fetchone()['completed_orders']

            cur.execute("""
                SELECT COUNT(*) AS total_reports 
                FROM reports r JOIN orders o ON o.order_id = r.order_id
                WHERE o.client_id = %s
            """, (client_id,))
            total_reports = cur.fetchone()['total_reports']

            return {
                'total_orders': total_orders,
                'active_orders': active_orders,
                'completed_orders': completed_orders,
                'total_reports': total_reports,
            }
    finally:
        conn.close()


def get_clients_orders_count() -> dict:
    """Количество заказов по каждому клиенту."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT client_id, COUNT(*) AS cnt
                FROM orders
                GROUP BY client_id
            """)
            return {row['client_id']: row['cnt'] for row in cur.fetchall()}
    finally:
        conn.close()


# ==================== ЗАКАЗЫ КЛИЕНТА ====================

def get_client_orders(client_id: int, limit: int = None) -> list[dict]:
    """Получить заказы клиента. limit — максимальное количество (если None — все)."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            sql = """
                SELECT o.order_id, o.vessel_code, o.order_date, o.status, o.total_price,
                       e.full_name AS employee_name
                FROM orders o
                LEFT JOIN employees e ON e.employee_id = o.employee_id
                WHERE o.client_id = %s
                ORDER BY o.order_date DESC
            """
            if limit:
                sql += f" LIMIT {int(limit)}"
            cur.execute(sql, (client_id,))
            return cur.fetchall()
    finally:
        conn.close()


# ==================== ОТЧЁТЫ КЛИЕНТА ====================

def get_client_reports(client_id: int) -> list[dict]:
    """Получить все отчёты клиента."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT r.report_id, r.report_date, r.file_path,
                       o.vessel_code, o.order_id
                FROM reports r
                JOIN orders o ON o.order_id = r.order_id
                WHERE o.client_id = %s
                ORDER BY r.report_date DESC
            """, (client_id,))
            return cur.fetchall()
    finally:
        conn.close()


# ==================== РЕЗУЛЬТАТЫ ИССЛЕДОВАНИЙ КЛИЕНТА ====================

def get_client_results(client_id: int) -> list[dict]:
    """Получить результаты исследований по всем заказам клиента."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rr.research_id, rr.result_value, rr.conclusion, rr.result_date,
                       o.order_id, o.vessel_code, o.order_date,
                       s.service_name
                FROM research_results rr
                JOIN order_services os ON os.order_service_id = rr.order_service_id
                JOIN orders o ON o.order_id = os.order_id
                JOIN services s ON s.service_id = os.service_id
                WHERE o.client_id = %s
                ORDER BY o.order_date DESC, s.service_name
            """, (client_id,))
            return cur.fetchall()
    finally:
        conn.close()


# ==================== СОЗДАНИЕ / ОБНОВЛЕНИЕ ====================

def create_client(client_type: str, name: str, phone: str = '', email: str = '',
                  login: str = '', password_hash: str = '', **kwargs) -> int:
    """Создать нового клиента. Возвращает client_id."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO clients (client_type, login, password_hash, phone, email, is_active)
                VALUES (%s, %s, %s, %s, %s, 1)
            """, (client_type, login or None, password_hash or None, phone, email))
            client_id = cur.lastrowid

            if client_type == 'ЮЛ':
                cur.execute("""
                    INSERT INTO legal_entities (client_id, company_name, address, inn, kpp,
                                                checking_account, bik, director_name, contact_person)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (client_id, name, kwargs.get('address', ''), kwargs.get('inn', ''),
                      kwargs.get('kpp', ''), kwargs.get('bank_account', ''),
                      kwargs.get('bik', ''), kwargs.get('director_name', ''),
                      kwargs.get('contact_person', '')))
            else:
                cur.execute("""
                    INSERT INTO individuals (client_id, full_name, birth_date,
                                             passport_series, passport_number)
                    VALUES (%s, %s, %s, %s, %s)
                """, (client_id, name, kwargs.get('birth_date'),
                      kwargs.get('passport_series', ''), kwargs.get('passport_number', '')))

            conn.commit()
            return client_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_client(client_id: int, client_type: str, name: str, phone: str = '',
                  email: str = '', login: str = '', password_hash: str = '', **kwargs):
    """Обновить данные клиента."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE clients SET client_type = %s, login = %s, password_hash = %s,
                                   phone = %s, email = %s
                WHERE client_id = %s
            """, (client_type, login or None, password_hash or None, phone, email, client_id))

            if client_type == 'ЮЛ':
                cur.execute("""
                    INSERT INTO legal_entities (client_id, company_name, address, inn, kpp,
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
                """, (client_id, name, kwargs.get('address', ''), kwargs.get('inn', ''),
                      kwargs.get('kpp', ''), kwargs.get('bank_account', ''),
                      kwargs.get('bik', ''), kwargs.get('director_name', ''),
                      kwargs.get('contact_person', '')))
            else:
                cur.execute("""
                    INSERT INTO individuals (client_id, full_name, birth_date,
                                             passport_series, passport_number)
                    VALUES (%s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                        full_name = VALUES(full_name),
                        birth_date = VALUES(birth_date),
                        passport_series = VALUES(passport_series),
                        passport_number = VALUES(passport_number)
                """, (client_id, name, kwargs.get('birth_date'),
                      kwargs.get('passport_series', ''), kwargs.get('passport_number', '')))

            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ==================== АЛИАСЫ для совместимости ====================

def add_client(data: dict) -> int:
    """Обёртка для client_dialog.py — принимает словарь."""
    return create_client(
        client_type=data.get('client_type', 'ЮЛ'),
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        login=data.get('login', ''),
        password_hash=data.get('password_hash', ''),
        **{k: v for k, v in data.items() if k not in ('client_type', 'name', 'phone', 'email', 'login', 'password_hash')}
    )


def update_client_data(data: dict):
    """Обёртка для client_dialog.py — принимает словарь."""
    update_client(
        client_id=data.get('client_id'),
        client_type=data.get('client_type', 'ЮЛ'),
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        email=data.get('email', ''),
        login=data.get('login', ''),
        password_hash=data.get('password_hash', ''),
        **{k: v for k, v in data.items() if k not in ('client_id', 'client_type', 'name', 'phone', 'email', 'login', 'password_hash')}
    )

get_client_info = get_client_by_id