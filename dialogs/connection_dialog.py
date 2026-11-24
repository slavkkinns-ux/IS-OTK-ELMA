"""Диалог подключения к БД с автопроверкой структуры."""

from __future__ import annotations

import logging
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject
from services.connection_service import ConnectionService

logger = logging.getLogger(__name__)


class _Worker(QObject):
    """Фоновая проверка доступности БД."""
    finished = pyqtSignal(bool)

    def __init__(self, connection_service: ConnectionService, parent=None):
        super().__init__(parent)
        self.connection_service = connection_service

    def check(self):
        result = self.connection_service.is_db_available()
        self.finished.emit(result)


class ConnectionDialog(QDialog):
    """Диалог подключения к базе данных с автоповтором."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к базе данных")
        self.setFixedSize(420, 220)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

        self.connection_service = ConnectionService()

        self._attempt = 0
        self._max_attempts = 5
        self._thread = None
        self._worker = None

        self._build_ui()
        self._start_check()

    def _build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Подключение к базе данных...")
        title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #174A7E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        self.lblConfig = QLabel(f"Параметры: {self.connection_service.get_config_info()}")
        self.lblConfig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblConfig.setStyleSheet("color: #666; font-size: 9pt;")
        root.addWidget(self.lblConfig)

        self.lblStatus = QLabel("Проверка доступности сервера...")
        self.lblStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblStatus.setWordWrap(True)
        root.addWidget(self.lblStatus)

        self.progress = QProgressBar()
        self.progress.setRange(0, self._max_attempts)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        # Кнопки
        btns = QHBoxLayout()
        self.btnRetry = QPushButton("🔄 Повторить")
        self.btnRetry.clicked.connect(self._on_retry)
        self.btnSettings = QPushButton("⚙ Настройки")
        self.btnSettings.clicked.connect(self._on_settings)
        self.btnExit = QPushButton("✕ Выйти")
        self.btnExit.clicked.connect(self.reject)
        btns.addWidget(self.btnRetry)
        btns.addWidget(self.btnSettings)
        btns.addWidget(self.btnExit)
        root.addLayout(btns)

        self.btnRetry.setEnabled(False)
        self.btnSettings.setEnabled(False)

    def _start_check(self):
        """Запустить проверку в фоне."""
        self._attempt += 1
        self.lblStatus.setText(
            f"Попытка {self._attempt} из {self._max_attempts}...\n"
            f"Проверка доступности сервера MySQL."
        )
        self.progress.setValue(self._attempt - 1)
        self.btnRetry.setEnabled(False)
        self.btnSettings.setEnabled(False)

        self._thread = QThread(self)
        self._worker = _Worker(self.connection_service)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.check)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_check_finished(self, available: bool):
        """Обработка результата проверки."""
        if available:
            try:
                self.connection_service.connect()
                self.lblStatus.setText("Подключение установлено.\nПроверка и миграция БД...")
                self.progress.setValue(self._max_attempts)

                try:
                    schema_info = self.connection_service.ensure_schema()
                    logger.info("DB Migration: %s", schema_info)
                except Exception as e:
                    self.lblStatus.setText(f"Ошибка при миграции БД:\n{e}")
                    self.btnRetry.setEnabled(True)
                    self.btnSettings.setEnabled(True)
                    return

                QTimer.singleShot(400, self.accept)
            except Exception as e:
                self._show_error(f"Ошибка подключения:\n{e}\n\nПроверьте параметры в config.py")
        else:
            if self._attempt < self._max_attempts:
                QTimer.singleShot(2000, self._start_check)
            else:
                self._show_error(
                    "Сервер MySQL недоступен.\n\n"
                    "Убедитесь, что:\n"
                    "• MySQL запущен\n"
                    "• Параметры в config.py верны\n"
                    "• Сеть доступна"
                )

    def _show_error(self, message: str):
        self.progress.setValue(self._max_attempts)
        self.lblStatus.setText(message)
        self.lblStatus.setStyleSheet("color: #B03A2E;")
        self.btnRetry.setEnabled(True)
        self.btnSettings.setEnabled(True)

    def _on_retry(self):
        self._attempt = 0
        self.lblStatus.setStyleSheet("")
        self._start_check()

    def _on_settings(self):
        import subprocess
        import sys
        import os
        import json
        base_dir = os.path.dirname(os.path.dirname(__file__))
        config_json_path = os.path.join(base_dir, 'config.json')
        
        # Если config.json не существует — создаём пустой шаблон
        if not os.path.exists(config_json_path):
            default_config = {
                "host": "localhost",
                "port": 3306,
                "user": "root",
                "password": "",
                "database": "elma",
                "charset": "utf8mb4"
            }
            try:
                with open(config_json_path, 'w', encoding='utf-8') as f:
                    json.dump(default_config, f, ensure_ascii=False, indent=4)
            except Exception as e:
                self._show_error(f"Не удалось создать config.json:\n{e}")
                return
        
        # Открываем config.json в редакторе по умолчанию
        if sys.platform == 'win32':
            os.startfile(config_json_path)
        else:
            subprocess.Popen(['xdg-open', config_json_path])

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        event.accept()


__all__ = ["ConnectionDialog"]
