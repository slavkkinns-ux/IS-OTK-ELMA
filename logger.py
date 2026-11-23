"""Настройка логирования приложения.

Настраивается корневой логгер, поэтому записи из services.*, db.* и widgets.*
попадают в тот же файл и консоль, что и записи логгера IS_OTK.
"""
from __future__ import annotations

import logging
import os
import sys
from datetime import datetime

# Папка логов: на уровень выше папки проекта
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
LOG_FORMAT = '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
APP_LOGGER_NAME = "IS_OTK"

_configured = False


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Один раз настроить корневой логгер (файл + консоль). Возвращает логгер IS_OTK."""
    global _configured
    if not _configured:
        root = logging.getLogger()
        root.setLevel(level)
        formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

        # В режиме без консоли (pythonw, exe без окна) sys.stderr равен None
        if sys.stderr is not None:
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            root.addHandler(console)

        try:
            os.makedirs(LOG_DIR, exist_ok=True)
            log_file = os.path.join(
                LOG_DIR, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setFormatter(formatter)
            root.addHandler(file_handler)
        except OSError as exc:
            root.warning("Файл лога недоступен (%s), запись только в консоль", exc)

        _configured = True
    return logging.getLogger(APP_LOGGER_NAME)


def setup_logger(name: str = APP_LOGGER_NAME, level: int = logging.INFO) -> logging.Logger:
    """Совместимость со старым API: настроить логирование и вернуть логгер name."""
    setup_logging(level)
    return logging.getLogger(name)


def get_logger(name: str) -> logging.Logger:
    """Получить логгер модуля с гарантией, что логирование настроено."""
    setup_logging()
    return logging.getLogger(name)


# Глобальный логгер приложения
app_logger = setup_logging()
