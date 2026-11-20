"""Подключение к MySQL с обработкой ошибок и автоповтором."""
import pymysql
import time

_connection = None
_config = None
_last_error = None


def _load_config(force_reload: bool = False):
    """Загружает параметры подключения из config.py.
    Поддерживает формат: DB_CONFIG = {'host': ..., 'user': ..., ...}
    """
    global _config
    if _config is not None and not force_reload:
        return _config

    # Значения по умолчанию
    cfg = {
        'host': 'localhost',
        'port': 3306,
        'user': 'root',
        'password': '',
        'database': 'is_otk',
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'connect_timeout': 5,
    }

    try:
        import config
    except ImportError:
        _config = cfg
        return _config

    # === Формат 1: словарь DB_CONFIG ===
    if hasattr(config, 'DB_CONFIG') and isinstance(config.DB_CONFIG, dict):
        for key in ('host', 'port', 'user', 'password', 'database', 'charset'):
            if key in config.DB_CONFIG:
                cfg[key] = config.DB_CONFIG[key]

    # === Формат 2: отдельные константы (DB_HOST, DB_USER ...) ===
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
    """Строка с текущими параметрами (без пароля) — для диагностики."""
    c = _load_config()
    return f"{c['user']}@{c['host']}:{c['port']} / {c['database']}"


def get_last_error() -> str | None:
    return _last_error


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


def close_connection():
    global _connection
    try:
        if _connection and _connection.open:
            _connection.close()
    except Exception:
        pass
    _connection = None


# Для обратной совместимости
def connect():
    return get_connection()


def close():
    close_connection()