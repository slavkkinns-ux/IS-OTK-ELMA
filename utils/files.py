"""Открытие и печать файлов средствами операционной системы."""

from __future__ import annotations

import os
import subprocess
import sys


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
