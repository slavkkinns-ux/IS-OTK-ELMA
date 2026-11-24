"""Управление сессией пользователя."""
import logging
import os
import json

SESSION_FILE = "session.json"
FIRST_LOGIN_FILE = "first_login.json"

logger = logging.getLogger(__name__)


class Role:
    MANAGER = "manager"
    LAB_TECHNICIAN = "lab_technician"
    CONTROLLER = "controller"
    ADMIN = "admin"
    CLIENT = "client"


# Маппинг: русские названия ролей из БД → внутренние коды
ROLE_NAME_MAP = {
    'Администратор': Role.ADMIN,
    'Менеджер': Role.MANAGER,
    'Менеджер по работе с клиентами': Role.MANAGER,
    'Лаборант': Role.LAB_TECHNICIAN,
    'Контролёр': Role.CONTROLLER,
    'Контроллер': Role.CONTROLLER,
    'Клиент': Role.CLIENT,
    'admin': Role.ADMIN,
    'manager': Role.MANAGER,
    'lab_technician': Role.LAB_TECHNICIAN,
    'controller': Role.CONTROLLER,
    'client': Role.CLIENT,
}

ROLE_DISPLAY_NAMES = {
    Role.MANAGER: "Менеджер по работе с клиентами",
    Role.LAB_TECHNICIAN: "Лаборант",
    Role.CONTROLLER: "Контролёр",
    Role.ADMIN: "Администратор",
    Role.CLIENT: "Клиент",
}

ROLE_PERMISSIONS = {
    Role.MANAGER: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": False, "can_view_reports": False,
        "can_do_research": False, "can_manage_employees": False,
    },
    Role.LAB_TECHNICIAN: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True, "can_manage_employees": False,
    },
    Role.CONTROLLER: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True, "can_manage_employees": False,
    },
    Role.ADMIN: {
        "can_create_order": True, "can_view_orders": True,
        "can_create_reports": True, "can_view_reports": True,
        "can_do_research": True, "can_manage_employees": True,
    },
    Role.CLIENT: {
        "can_create_order": False, "can_view_orders": True,
        "can_create_reports": False, "can_view_reports": True,
        "can_do_research": False, "can_manage_employees": False,
    },
}


class Session:
    _current_user = None

    @classmethod
    def init(cls):
        cls._load_from_file()

    @classmethod
    def is_first_login(cls) -> bool:
        """Проверить, первый ли это вход пользователя."""
        if not cls._current_user:
            return True
        user_id = cls._current_user.get("user_id")
        if not user_id:
            return True
        try:
            if not os.path.exists(FIRST_LOGIN_FILE):
                return True
            with open(FIRST_LOGIN_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return str(user_id) not in data.get("logged_in_users", [])
        except Exception:
            return True

    @classmethod
    def mark_first_login_done(cls):
        """Отметить, что первый вход уже пройден для текущего пользователя."""
        if not cls._current_user:
            return
        user_id = cls._current_user.get("user_id")
        if not user_id:
            return
        try:
            data = {"logged_in_users": []}
            if os.path.exists(FIRST_LOGIN_FILE):
                with open(FIRST_LOGIN_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            logged_in = set(data.get("logged_in_users", []))
            logged_in.add(str(user_id))
            data["logged_in_users"] = list(logged_in)
            with open(FIRST_LOGIN_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            logger.error("Ошибка сохранения флага первого входа: %s", exc)

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
        return cls._current_user.get("display_name", cls._current_user.get("login", ""))

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
        except Exception as exc:
            logger.error("Ошибка сохранения сессии: %s", exc)

    @classmethod
    def _load_from_file(cls):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                # Нормализуем роль при загрузке из файла
                if 'role' in data:
                    data['role'] = ROLE_NAME_MAP.get(data['role'], data['role'])
                cls._current_user = data
            except Exception:
                cls._current_user = None