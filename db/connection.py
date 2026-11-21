"""Подключение к MySQL с обработкой ошибок и автоповтором."""
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

    # Формат 1: словарь DB_CONFIG
    if hasattr(config, 'DB_CONFIG') and isinstance(config.DB_CONFIG, dict):
        for key in ('host', 'port', 'user', 'password', 'database', 'charset'):
            if key in config.DB_CONFIG:
                cfg[key] = config.DB_CONFIG[key]
    # Формат 2: отдельные константы
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
            host=cfg['host'],
            port=cfg['port'],
            user=cfg['user'],
            password=cfg['password'],
            charset='utf8mb4',
            connect_timeout=5,
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
    """Проверяет доступность БД. Возвращает (успех, текст ошибки)."""
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


def ensure_schema() -> str:
    """Проверяет наличие всех нужных таблиц и создаёт недостающие + админа."""
    from db.schema import SCHEMA_SQL, REQUIRED_TABLES

    # Правильный SHA-256 хэш пароля "12345"
    ADMIN_PASSWORD_HASH = hashlib.sha256('12345'.encode()).hexdigest()

    # Шаг 1: Проверяем/создаём базу данных
    db_info = ensure_database()

    # Шаг 2: Подключаемся к конкретной БД
    conn = get_connection()
    created = []
    already_exists = []

    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES")
            existing = {list(row.values())[0] for row in cur.fetchall()}

            missing = [t for t in REQUIRED_TABLES if t not in existing]
            if not missing:
                # Таблицы есть — проверяем/обновляем админа
                cur.execute("SELECT password_hash FROM employees WHERE login = 'admin' LIMIT 1")
                row = cur.fetchone()
                if row is None:
                    cur.execute(
                        "INSERT INTO employees (full_name, login, password_hash, role, is_active) "
                        "VALUES ('Администратор системы', 'admin', %s, 'Администратор', 1)",
                        (ADMIN_PASSWORD_HASH,)
                    )
                    conn.commit()
                elif row['password_hash'] != ADMIN_PASSWORD_HASH:
                    cur.execute(
                        "UPDATE employees SET password_hash = %s WHERE login = 'admin'",
                        (ADMIN_PASSWORD_HASH,)
                    )
                    conn.commit()
                return f"{db_info}\nВсе таблицы уже существуют. Администратор проверен."

            # Создаём таблицы
            for statement in SCHEMA_SQL.split(';'):
                stmt = statement.strip()
                if stmt and not stmt.startswith('--'):
                    cur.execute(stmt)
            conn.commit()

            cur.execute("SHOW TABLES")
            after = {list(row.values())[0] for row in cur.fetchall()}

            for t in REQUIRED_TABLES:
                if t in after and t not in existing:
                    created.append(t)
                elif t in existing:
                    already_exists.append(t)

            # Создаём админа
            cur.execute("SELECT 1 FROM employees WHERE login = 'admin' LIMIT 1")
            if cur.fetchone() is None:
                cur.execute(
                    "INSERT INTO employees (full_name, login, password_hash, role, is_active) "
                    "VALUES ('Администратор системы', 'admin', %s, 'Администратор', 1)",
                    (ADMIN_PASSWORD_HASH,)
                )
                conn.commit()

    except Exception as e:
        conn.rollback()
        raise

    parts = [db_info]
    if created:
        parts.append(f"Созданы таблицы: {', '.join(created)}")
    if already_exists:
        parts.append(f"Уже существовали: {', '.join(already_exists)}")
    parts.append("Администратор: login=admin, password=12345")
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