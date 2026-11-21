"""Подключение к MySQL с полной проверкой и миграцией БД."""
import pymysql
import time
import hashlib

_connection = None
_config = None
_last_error = None


def _load_config(force_reload: bool = False):
    """Загружает параметры подключения из config.py."""
    global _config
    if _config is not None and not force_reload:
        return _config

    cfg = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'elma',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': 5,
    }

    try:
        import config
    except ImportError:
        _config = cfg
        return _config

    if hasattr(config, 'DB_CONFIG') and isinstance(config.DB_CONFIG, dict):
        for key in ('host', 'port', 'user', 'password', 'database', 'charset'):
            if key in config.DB_CONFIG:
                cfg[key] = config.DB_CONFIG[key]
    else:
        aliases = {
            'host': ('DB_HOST', 'MYSQL_HOST', 'HOST'),
            'port': ('DB_PORT', 'MYSQL_PORT', 'PORT'),
            'user': ('DB_USER', 'MYSQL_USER', 'USER', 'USERNAME'),
            'password': ('DB_PASSWORD', 'MYSQL_PASSWORD', 'PASSWORD', 'PASSWD'),
            'database': ('DB_NAME', 'MYSQL_DATABASE', 'MYSQL_DB', 'DATABASE', 'DB'),
            'charset': ('DB_CHARSET', 'CHARSET'),
        }
        for key, names in aliases.items():
            for n in names:
                if hasattr(config, n):
                    cfg[key] = getattr(config, n)
                    break

    cfg['port'] = int(cfg['port'])
    _config = cfg
    return _config


def get_config_info() -> str:
    c = _load_config()
    return f"{c['user']}@{c['host']}:{c['port']} / {c['database']}"


def get_last_error() -> str | None:
    return _last_error


def ensure_database() -> str:
    """Проверяет наличие БД и создаёт её, если нет."""
    cfg = _load_config()
    db_name = cfg['database']
    try:
        conn = pymysql.connect(
            host=cfg['host'], port=cfg['port'], user=cfg['user'],
            password=cfg['password'], charset='utf8mb4', connect_timeout=5,
        )
        with conn.cursor() as cur:
            cur.execute(f"SHOW DATABASES LIKE '{db_name}'")
            exists = cur.fetchone() is not None
            if not exists:
                cur.execute(
                    f"CREATE DATABASE `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
                )
                conn.commit()
                conn.close()
                return f"База данных '{db_name}' создана."
            else:
                conn.close()
                return f"База данных '{db_name}' уже существует."
    except Exception as e:
        raise RuntimeError(f"Не удалось создать базу данных '{db_name}': {e}")


def get_connection():
    """Возвращает активное соединение, при обрыве — пересоздаёт."""
    global _connection, _last_error
    try:
        if _connection is None or not _connection.open:
            _connection = pymysql.connect(**_load_config())
        else:
            _connection.ping(reconnect=True)
        _last_error = None
        return _connection
    except Exception as e:
        _last_error = str(e)
        raise


def check_db() -> tuple:
    """Проверяет доступность БД."""
    global _last_error
    try:
        conn = pymysql.connect(**_load_config(force_reload=True))
        conn.close()
        _last_error = None
        return True, None
    except Exception as e:
        _last_error = str(e)
        return False, str(e)


def is_db_available() -> bool:
    ok, _ = check_db()
    return ok


def connect_with_retry(max_attempts: int = 3, delay: float = 1.0) -> bool:
    for attempt in range(1, max_attempts + 1):
        try:
            get_connection()
            return True
        except Exception:
            if attempt < max_attempts:
                time.sleep(delay)
    return False


def _get_existing_columns(conn, table: str) -> set:
    """Получить множество существующих колонок таблицы."""
    try:
        with conn.cursor() as cur:
            cur.execute(f"SHOW COLUMNS FROM `{table}`")
            return {row['Field'] for row in cur.fetchall()}
    except Exception:
        return set()


def ensure_columns() -> list[str]:
    """Проверяет все таблицы и добавляет недостающие колонки.
    Возвращает список выполненных ALTER TABLE."""
    from db.schema import TABLE_COLUMNS

    conn = get_connection()
    actions = []

    try:
        with conn.cursor() as cur:
            # Проверяем, какие таблицы есть
            cur.execute("SHOW TABLES")
            existing_tables = {list(row.values())[0] for row in cur.fetchall()}

            for table, columns in TABLE_COLUMNS.items():
                if table not in existing_tables:
                    continue  # Таблицы нет — её создаст ensure_schema()

                existing_cols = _get_existing_columns(conn, table)
                for col_name, col_def in columns.items():
                    if col_name not in existing_cols:
                        # Добавляем колонку
                        # Для PRIMARY KEY колонок — только если таблица пустая
                        if 'PRIMARY KEY' in col_def:
                            cur.execute(f"SELECT COUNT(*) AS cnt FROM `{table}`")
                            if cur.fetchone()['cnt'] > 0:
                                actions.append(f"⚠ Таблица {table} не пуста, колонка {col_name} (PK) не добавлена")
                                continue

                        sql = f"ALTER TABLE `{table}` ADD COLUMN `{col_name}` {col_def}"
                        try:
                            cur.execute(sql)
                            actions.append(f"+ {table}.{col_name}")
                        except Exception as e:
                            actions.append(f"✗ {table}.{col_name}: {e}")

            conn.commit()
    except Exception as e:
        conn.rollback()
        raise

    return actions


def ensure_schema() -> str:
    """Полная проверка и миграция БД:
    1. Создаёт БД, если нет
    2. Создаёт таблицы, если нет
    3. Добавляет недостающие колонки
    4. Создаёт администратора, если нет
    """
    from db.schema import SCHEMA_SQL, REQUIRED_TABLES

    ADMIN_PASSWORD_HASH = hashlib.sha256('12345'.encode()).hexdigest()

    # Шаг 1: БД
    db_info = ensure_database()

    # Шаг 2: Таблицы
    conn = get_connection()
    created_tables = []
    existing_tables = []

    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            existing = {list(row.values())[0] for row in cur.fetchall()}

            missing = [t for t in REQUIRED_TABLES if t not in existing]
            if missing:
                for statement in SCHEMA_SQL.split(';'):
                    stmt = statement.strip()
                    if stmt and not stmt.startswith('--'):
                        try:
                            cur.execute(stmt)
                        except Exception:
                            pass  # Ошибки игнорируем — таблицы могут уже быть
                conn.commit()

                cur.execute("SHOW TABLES")
                after = {list(row.values())[0] for row in cur.fetchall()}
                for t in REQUIRED_TABLES:
                    if t in after and t not in existing:
                        created_tables.append(t)
                    elif t in existing:
                        existing_tables.append(t)
            else:
                existing_tables = list(existing & set(REQUIRED_TABLES))

            # Шаг 3: Колонки (миграция)
            column_actions = ensure_columns()

            # Шаг 4: Администратор
            cur.execute("SELECT password_hash FROM employees WHERE login = 'admin' LIMIT 1")
            row = cur.fetchone()
            admin_status = ""
            if row is None:
                cur.execute(
                    "INSERT INTO employees (full_name, login, password_hash, role, is_active) "
                    "VALUES ('Администратор системы', 'admin', %s, 'Администратор', 1)",
                    (ADMIN_PASSWORD_HASH,)
                )
                conn.commit()
                admin_status = "\n✓ Администратор создан (login=admin, password=12345)"
            elif row['password_hash'] != ADMIN_PASSWORD_HASH:
                cur.execute(
                    "UPDATE employees SET password_hash = %s WHERE login = 'admin'",
                    (ADMIN_PASSWORD_HASH,)
                )
                conn.commit()
                admin_status = "\n✓ Пароль администратора обновлён"

    except Exception as e:
        conn.rollback()
        raise

    # Формируем отчёт
    parts = [db_info]
    if created_tables:
        parts.append(f"Созданы таблицы: {', '.join(created_tables)}")
    if column_actions:
        parts.append("Миграция колонок:")
        parts.extend(f"  {a}" for a in column_actions)
    if admin_status:
        parts.append(admin_status)
    if not created_tables and not column_actions and not admin_status:
        parts.append("Всё актуально. Приложение готово к работе.")

    return '\n'.join(parts)


def close_connection():
    global _connection
    try:
        if _connection and _connection.open:
            _connection.close()
    except Exception:
        pass
    _connection = None


def connect():
    return get_connection()


def close():
    close_connection()