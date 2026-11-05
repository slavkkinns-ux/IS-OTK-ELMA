import json
import os

SESSION_FILE = "session.json"

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
    def set_user(cls, login, role):
        cls._current_user = {"login": login, "role": role}
        cls._save_to_file()

    @classmethod
    def get_user(cls):
        return cls._current_user

    @classmethod
    def clear(cls):
        cls._current_user = None
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)

    @classmethod
    def is_authenticated(cls):
        return cls._current_user is not None