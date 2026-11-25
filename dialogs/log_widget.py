"""Окно просмотра логов приложения (только для администратора)."""

from __future__ import annotations

import os
from datetime import datetime

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from logger import LOG_DIR
from widgets.dialog_helpers import show_error, show_info
from widgets.styles import TITLE_STYLE

_LOG_VIEW_STYLE = """
    QTextEdit {
        background-color: #1e1e1e;
        color: #d4d4d4;
        font-family: Consolas, 'Courier New', monospace;
        font-size: 10pt;
        border: 1px solid #CBD7E4;
        border-radius: 4px;
        padding: 5px;
    }
"""


class LogWidget(QWidget):
    """Показывает содержимое последнего лог-файла, умеет очищать вид и сохранять в файл."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Логи приложения")
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        title = QLabel("Логи приложения")
        title.setStyleSheet(TITLE_STYLE)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet(_LOG_VIEW_STYLE)
        layout.addWidget(self.text_edit)

        btns = QHBoxLayout()
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.text_edit.clear)
        btn_save = QPushButton("Сохранить в файл")
        btn_save.clicked.connect(self._save_logs)
        btn_close = QPushButton("Закрыть")
        btn_close.clicked.connect(self.close)
        btns.addWidget(btn_clear)
        btns.addWidget(btn_save)
        btns.addStretch()
        btns.addWidget(btn_close)
        layout.addLayout(btns)

        self._load_latest_log()

    def _load_latest_log(self) -> None:
        """Загрузить последний лог-файл (имена app_ГГГГММДД_ЧЧММСС.log сортируются по дате)."""
        if not os.path.isdir(LOG_DIR):
            self.text_edit.setPlainText("Папка logs не найдена.")
            return

        log_files = sorted((f for f in os.listdir(LOG_DIR) if f.endswith(".log")), reverse=True)
        if not log_files:
            self.text_edit.setPlainText("Лог-файлы не найдены.")
            return

        try:
            with open(os.path.join(LOG_DIR, log_files[0]), encoding="utf-8") as f:
                self.text_edit.setPlainText(f.read())
            scrollbar = self.text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except OSError as exc:
            self.text_edit.setPlainText(f"Ошибка чтения лога:\n{exc}")

    def _save_logs(self) -> None:
        default_name = f"logs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить логи", default_name, "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.text_edit.toPlainText())
            show_info(self, "Готово", f"Логи сохранены в:\n{path}")
        except OSError as exc:
            show_error(self, "Ошибка", f"Не удалось сохранить:\n{exc}")


__all__ = ["LogWidget"]
