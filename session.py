"""Управление сессией пользователя."""
import os
import json

SESSION_FILE = "session.json"


class Role:
    MANAGER = "manager"
    LAB_TECHNICIAN = "lab_technician"
    CONTROLLER = "controller"
    ADMIN = "admin"
    CLIENT = "client"


ROLE_DISPLAY_NAMES = {
    Role.MANAGER: "Менеджер по работе с клиентами",
    Role.LAB_TECHNICIAN: "Лаборант",
    Role.CONTROLLER: "Контролёр",
    Role.ADMIN: "Администратор",
    Role.CLIENT: "Клиент",
}

ROLE_PERMISSIONS = {
    Role.MANAGER: {
        "can_create_order": True, "can_view_orders": False,
        "can_create_reports": False, "can_view_reports": False,
        "can_do_research": False,
    },
    Role.LAB_TECHNICIAN: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True,
    },
    Role.CONTROLLER: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True,
    },
    Role.ADMIN: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True,
    },
    Role.CLIENT: {
        "can_create_order": False, "can_view_orders": True,
        "can_create_reports": False, "can_view_reports": True,
        "can_do_research": False,
    },
}


class Session:
    _current_user = None

    @classmethod
    def init(cls):
        """Загрузить сессию из файла при запуске приложения."""
        cls._load_from_file()

    @classmethod
    def set_user(cls, login, role, display_name=None, user_id=None,
                 user_type='employee', remember=True):
        """Установить текущего пользователя.

        remember=True  — сохранить в файл (галочка "Запомнить меня" включена)
        remember=False — НЕ сохранять в файл (галочка выключена)
        """
        cls._current_user = {
            "login": login,
            "role": role,
            "display_name": display_name or login.capitalize(),
            "user_id": user_id,
            "user_type": user_type,
        }
        if remember:
            cls._save_to_file()
        else:
            # Если файл был от прошлого входа — удаляем его
            if os.path.exists(SESSION_FILE):
                try:
                    os.remove(SESSION_FILE)
                except OSError:
                    pass

    @classmethod
    def get_user(cls):
        return cls._current_user

    @classmethod
    def get_user_id(cls):
        return cls._current_user.get("user_id") if cls._current_user else None

    @classmethod
    def get_user_type(cls):
        return cls._current_user.get("user_type", "employee") if cls._current_user else "employee"

    @classmethod
    def get_role(cls):
        return cls._current_user.get("role") if cls._current_user else None

    @classmethod
    def get_display_name(cls):
        if not cls._current_user:
            return ""
        return cls._current_user.get("display_name",
                                     cls._current_user.get("login", ""))

    @classmethod
    def get_role_display_name(cls):
        return ROLE_DISPLAY_NAMES.get(cls.get_role(), "Неизвестная роль")

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        role = cls.get_role()
        if not role:
            return False
        return ROLE_PERMISSIONS.get(role, {}).get(permission, False)

    @classmethod
    def clear(cls):
        """Выйти из системы — очистить память и удалить файл сессии."""
        cls._current_user = None
        if os.path.exists(SESSION_FILE):
            try:
                os.remove(SESSION_FILE)
            except OSError:
                pass

    @classmethod
    def is_authenticated(cls):
        return cls._current_user is not None

    @classmethod
    def _save_to_file(cls):
        try:
            with open(SESSION_FILE, 'w', encoding='utf-8') as f:
                json.dump(cls._current_user, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения сессии: {e}")

    @classmethod
    def _load_from_file(cls):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    cls._current_user = json.load(f)
            except Exception:
                cls._current_user = None