"""Работа с файлами и ресурсами (утилиты путей, открытие, печать)."""

from __future__ import annotations

import os
import subprocess
import sys


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

    На Windows пытается использовать системную команду печати. Если в системе
    нет приложения, зарегистрированного для печати PDF (WinError 1155),
    файл открывается в приложении по умолчанию, а пользователю предлагается
    распечатать его вручную.

    Raises:
        FileNotFoundError: Если файл не существует.
        RuntimeError: Если не удалось отправить на печать автоматически.
    """
    if not path or not os.path.exists(path):
        raise FileNotFoundError(f"Файл не найден: {path}")
    if sys.platform == "win32":
        try:
            os.startfile(path, "print")
        except OSError as e:
            # Нет приложения для автоматической печати PDF — открываем файл
            # в приложении по умолчанию и просим распечатать вручную.
            try:
                os.startfile(path)
            except OSError:
                pass
            raise RuntimeError(
                f"Не удалось автоматически отправить файл на печать.\n"
                f"Файл открыт в приложении по умолчанию. "
                f"Распечатайте его вручную (Ctrl+P).\n\n"
                f"Подробности: {e}"
            )
    else:
        subprocess.Popen(["lp", path])


__all__ = ["open_file", "print_file"]
