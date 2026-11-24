"""Работа с файлами и ресурсами (утилиты путей, открытие, печать)."""

from __future__ import annotations

import os
import sys
import subprocess


def get_resource_path(relative_path: str) -> str:
    """Вернуть абсолютный путь к ресурсу (работает и в dev, и в PyInstaller EXE).

    При запуске из EXE (PyInstaller --onefile) ресурсы распаковываются
    во временную папку sys._MEIPASS. В разработке — путь относительно корня проекта.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Запуск из собранного EXE
        base_path = sys._MEIPASS
    else:
        # Разработка: корень проекта (родительская папка этого файла -> utils -> project_root)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


def open_file(path: str) -> None:
    """Открыть файл в приложении по умолчанию.

    Raises:
        FileNotFoundError: Если файл не существует.
    """
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    if sys.platform == "win32":
        os.startfile(path)
    elif sys.platform == "darwin":
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])


def print_file(path: str) -> None:
    """Отправить файл на печать.

    Raises:
        FileNotFoundError: Если файл не существует.
    """
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    if sys.platform == "win32":
        os.startfile(path, "print")
    else:
        subprocess.Popen(["lp", path])


__all__ = ["open_file", "print_file"]
