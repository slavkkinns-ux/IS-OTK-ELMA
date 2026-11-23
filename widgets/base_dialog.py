"""Базовый класс диалогов: корневой layout, панель кнопок, обработка ошибок сохранения."""

from __future__ import annotations

from typing import Callable

from PyQt6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QVBoxLayout, QWidget

from widgets.dialog_helpers import show_error, show_info, show_question, show_warning


class BaseDialog(QDialog):
    """Диалог с общим каркасом.

    Подкласс добавляет свои виджеты в ``self.root`` (QVBoxLayout), затем вызывает
    ``add_save_cancel_buttons`` или ``add_close_button``.
    """

    def __init__(self, parent: QWidget | None = None, title: str = "", min_width: int = 480,
                 min_height: int | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(min_width)
        if min_height:
            self.setMinimumHeight(min_height)
        self.root = QVBoxLayout(self)
        self._save_callback: Callable[[], None] | None = None

    def add_save_cancel_buttons(
        self,
        on_save: Callable[[], None],
        save_text: str = "Сохранить",
        cancel_text: str = "Отмена",
    ) -> None:
        """Добавить кнопки «Сохранить» и «Отмена».

        ``on_save`` отвечает за закрытие диалога (``self.accept()``) при успехе.
        Исключения ValueError / PermissionError / Exception превращаются в сообщения.
        """
        self._save_callback = on_save
        row = QHBoxLayout()
        btn_save = QPushButton(save_text)
        btn_save.clicked.connect(self._on_save_clicked)
        btn_cancel = QPushButton(cancel_text)
        btn_cancel.clicked.connect(self.reject)
        row.addWidget(btn_save)
        row.addWidget(btn_cancel)
        self.root.addLayout(row)

    def add_close_button(self, text: str = "Закрыть") -> None:
        """Добавить кнопку «Закрыть» справа."""
        row = QHBoxLayout()
        row.addStretch()
        btn = QPushButton(text)
        btn.clicked.connect(self.accept)
        row.addWidget(btn)
        self.root.addLayout(row)

    def _on_save_clicked(self) -> None:
        if self._save_callback is None:
            return
        try:
            self._save_callback()
        except ValueError as exc:
            self.warn("Ошибка валидации", str(exc))
        except PermissionError as exc:
            self.fail("Отказ в доступе", str(exc))
        except Exception as exc:  # noqa: BLE001
            self.fail("Ошибка", f"Не удалось сохранить:\n{exc}")

    # Короткие обёртки над диалоговыми помощниками
    def info(self, title: str, message: str) -> None:
        show_info(self, title, message)

    def warn(self, title: str, message: str) -> None:
        show_warning(self, title, message)

    def fail(self, title: str, message: str) -> None:
        show_error(self, title, message)

    def ask(self, title: str, message: str) -> bool:
        return show_question(self, title, message)


__all__ = ["BaseDialog"]
