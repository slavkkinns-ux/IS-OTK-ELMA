"""Генерация паролей."""

from __future__ import annotations

import secrets
import string


def generate_password(length: int = 8) -> str:
    """Сгенерировать случайный пароль из букв и цифр (криптостойкий генератор)."""
    if length < 4:
        raise ValueError("Длина пароля должна быть не меньше 4 символов")
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))


__all__ = ["generate_password"]
