"""Настройка логирования для приложения."""
import logging
import os
from datetime import datetime


def setup_logger(name: str = "IS_OTK", level: int = logging.INFO) -> logging.Logger:
    """Настроить логгер с выводом в файл и консоль."""
    logger = logging.getLogger(name)
    
    # Если логгер уже настроен — возвращаем его
    if logger.handlers:
        return logger
    
    logger.setLevel(level)
    
    # Формат сообщений
    formatter = logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Вывод в консоль
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Вывод в файл
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(log_dir, f'app_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger


# Глобальный логгер приложения
app_logger = setup_logger("IS_OTK")