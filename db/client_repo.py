"""Репозиторий клиентов. MySQL."""
from db.connection import get_connection


def get_clients_by_type(client_type: str | None = None) -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            if client_type:
                cur.execute("""
                    SELECT c.client_id,
                           CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name ELSE i.full_name END AS name,
                           CASE WHEN c.client_type = 'ЮЛ' THEN le.contact_person ELSE i.full_name END AS contact_person,
                           c.client_type
                    FROM clients c
                    LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                    LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                    WHERE c.client_type = %s AND c.is_active = 1
                    ORDER BY name
                """, (client_type,))
            else:
                cur.execute("""
                    SELECT c.client_id,
                           CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name ELSE i.full_name END AS name,
                           CASE WHEN c.client_type = 'ЮЛ' THEN le.contact_person ELSE i.full_name END AS contact_person,
                           c.client_type
                    FROM clients c
                    LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                    LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                    WHERE c.is_active = 1
                    ORDER BY name
                """)
            return cur.fetchall()
    finally:
        conn.close()


def get_all_clients() -> list[dict]:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    c.client_id, c.client_type, c.phone, c.email,
                    CASE WHEN c.client_type = 'ЮЛ' THEN le.company_name
                         WHEN c.client_type = 'ФЛ' THEN i.full_name
                         ELSE 'Неизвестно' END AS name,
                    CASE WHEN c.client_type = 'ЮЛ' THEN le.inn
                         ELSE CONCAT(COALESCE(i.passport_series, ''), ' ', COALESCE(i.passport_number, ''))
                    END AS details,
                    CASE WHEN c.client_type = 'ЮЛ' THEN le.contact_person
                         WHEN c.client_type = 'ФЛ' THEN i.full_name
                         ELSE '' END AS contact_person
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id AND c.client_type = 'ЮЛ'
                LEFT JOIN individuals i ON i.client_id = c.client_id AND c.client_type = 'ФЛ'
                WHERE c.is_active = 1
                ORDER BY c.client_id DESC
            """)
            return cur.fetchall()
    finally:
        conn.close()


def add_client(data: dict) -> int:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO clients (client_type, phone, email, is_active)
                VALUES (%(client_type)s, %(phone)s, %(email)s, 1)
            """, data)
            client_id = cur.lastrowid

            if data['client_type'] == 'ЮЛ':
                cur.execute("""
                    INSERT INTO legal_entities 
                    (client_id, company_name, address, inn, kpp, checking_account, 
                     bik, director_name, contact_person)
                    VALUES (%(client_id)s, %(name)s, %(address)s, %(inn)s, %(kpp)s, 
                            %(bank_account)s, %(bik)s, %(director_name)s, %(contact_person)s)
                """, {**data, 'client_id': client_id})
            else:
                cur.execute("""
                    INSERT INTO individuals 
                    (client_id, full_name, birth_date, passport_series, passport_number)
                    VALUES (%(client_id)s, %(name)s, %(birth_date)s, 
                            %(passport_series)s, %(passport_number)s)
                """, {**data, 'client_id': client_id})

            conn.commit()
            return client_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_clients_stats() -> dict:
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) AS total_clients,
                       SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_clients,
                       COUNT(DISTINCT o.client_id) AS clients_with_orders
                FROM clients c
                LEFT JOIN orders o ON o.client_id = c.client_id
            """)
            row = cur.fetchone()
            return {
                'total_clients': row['total_clients'] or 0,
                'active_clients': row['active_clients'] or 0,
                'clients_with_orders': row['clients_with_orders'] or 0
            }
    finally:
        conn.close()

def get_client_details(client_id: int) -> dict:
    """Получить полные данные клиента для редактирования/просмотра."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.client_id, c.client_type, c.phone, c.email,
                       CASE WHEN c.client_type='ЮЛ' THEN le.company_name ELSE i.full_name END AS name,
                       le.address, le.inn, le.kpp, le.checking_account AS bank_account, le.bik,
                       le.director_name, le.contact_person,
                       i.birth_date, i.passport_series, i.passport_number
                FROM clients c
                LEFT JOIN legal_entities le ON le.client_id = c.client_id
                LEFT JOIN individuals i ON i.client_id = c.client_id
                WHERE c.client_id = %s
            """, (client_id,))
            return cur.fetchone()
    finally:
        conn.close()

def update_client(data: dict):
    """Обновить данные клиента."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                UPDATE clients SET phone = %(phone)s, email = %(email)s
                WHERE client_id = %(client_id)s
            """, data)
            if data['client_type'] == 'ЮЛ':
                cur.execute("""
                    UPDATE legal_entities
                    SET company_name=%(name)s, address=%(address)s, inn=%(inn)s, kpp=%(kpp)s,
                        checking_account=%(bank_account)s, bik=%(bik)s,
                        director_name=%(director_name)s, contact_person=%(contact_person)s
                    WHERE client_id = %(client_id)s
                """, data)
            else:
                cur.execute("""
                    UPDATE individuals
                    SET full_name=%(name)s, birth_date=%(birth_date)s,
                        passport_series=%(passport_series)s, passport_number=%(passport_number)s
                    WHERE client_id = %(client_id)s
                """, data)
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def get_clients_orders_count() -> dict:
    """Возвращает словарь {client_id: количество заказов}."""
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT c.client_id, COUNT(o.order_id) AS order_count
                FROM clients c
                LEFT JOIN orders o ON o.client_id = c.client_id
                WHERE c.is_active = 1
                GROUP BY c.client_id
            """)
            return {row['client_id']: row['order_count'] for row in cur.fetchall()}
    finally:
        conn.close()