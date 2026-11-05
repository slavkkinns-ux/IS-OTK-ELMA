import json
import os

SESSION_FILE = "session.json"

class Role:
    MANAGER = "manager"
    LAB_TECHNICIAN = "lab_technician"
    CONTROLLER = "controller"
    ADMIN = "admin"

ROLE_DISPLAY_NAMES = {
    Role.MANAGER: "Менеджер по работе с клиентами",
    Role.LAB_TECHNICIAN: "Лаборант",
    Role.CONTROLLER: "Контроллер",
    Role.ADMIN: "Администратор",
}

ROLE_PERMISSIONS = {
    Role.MANAGER: {
        "can_create_order": True,
        "can_view_orders": False,
        "can_create_reports": False,
        "can_view_reports": False,
        "can_do_research": False,
    },
    Role.LAB_TECHNICIAN: {
        "can_create_order": True,
        "can_view_orders": True,
        "can_create_reports": True,
        "can_view_reports": True,
        "can_do_research": True,
    },
    Role.CONTROLLER: {
        "can_create_order": True,
        "can_view_orders": True,
        "can_create_reports": True,
        "can_view_reports": True,
        "can_do_research": True,
    },
    Role.ADMIN: {
        "can_create_order": True,
        "can_view_orders": True,
        "can_create_reports": True,
        "can_view_reports": True,
        "can_do_research": True,
    },
}

class Session:
    _current_user = None

    @classmethod
    def _save_to_file(cls):
        if cls._current_user:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(cls._current_user, f, indent=2, ensure_ascii=False)

    @classmethod
    def _load_from_file(cls):
        if not os.path.exists(SESSION_FILE):
            return None
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                cls._current_user = data
                return data
        except (json.JSONDecodeError, IOError):
            return None

    @classmethod
    def init(cls):
        cls._load_from_file()

    @classmethod
    def set_user(cls, login, role, display_name=None, employee_id=None):
        cls._current_user = {
            "login": login,
            "role": role,
            "display_name": display_name or login.capitalize(),
            "employee_id": employee_id
        }
        cls._save_to_file()

    @classmethod
    def get_user(cls):
        return cls._current_user

    @classmethod
    def get_employee_id(cls):
        if cls._current_user:
            return cls._current_user.get("employee_id")
        return None

    @classmethod
    def get_role(cls):
        if cls._current_user:
            return cls._current_user.get("role")
        return None

    @classmethod
    def get_display_name(cls):
        if cls._current_user:
            return cls._current_user.get("display_name", cls._current_user.get("login", ""))
        return ""

    @classmethod
    def get_role_display_name(cls):
        role = cls.get_role()
        return ROLE_DISPLAY_NAMES.get(role, "Неизвестная роль")

    @classmethod
    def has_permission(cls, permission: str) -> bool:
        role = cls.get_role()
        if not role:
            return False
        perms = ROLE_PERMISSIONS.get(role, {})
        return perms.get(permission, False)

    @classmethod
    def clear(cls):
        cls._current_user = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    @classmethod
    def is_authenticated(cls):
        return cls._current_user is not None