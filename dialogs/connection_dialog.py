"""Диалог подключения к БД."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QGroupBox
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QObject
from db.connection import is_db_available, connect


class _Worker(QObject):
    """Фоновая проверка доступности БД."""
    finished = pyqtSignal(bool)

    def check(self):
        result = is_db_available()
        self.finished.emit(result)


class ConnectionDialog(QDialog):
    """Диалог подключения к БД с автоповтором."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к базе данных")
        self.setFixedSize(420, 220)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )
        # Сначала инициализируем атрибуты, потом строим UI
        self._attempt = 0
        self._max_attempts = 5
        self._build_ui()
        self._start_check()

    def _build_ui(self):
        root = QVBoxLayout(self)

        title = QLabel("Подключение к базе данных...")
        title.setStyleSheet("font-size: 13pt; font-weight: bold; color: #174A7E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

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

        from PyQt6.QtCore import QThread
        self._thread = QThread(self)
        self._worker = _Worker()
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.check)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_check_finished(self, available: bool):
        """Обработка результата проверки."""
        if available:
            # Пытаемся подключиться
            try:
                connect()
                self.lblStatus.setText("✅ Подключение установлено!")
                self.progress.setValue(self._max_attempts)
                self.accept()  # закрываем диалог с успехом
            except Exception as e:
                self.lblStatus.setText(
                    f"❌ Ошибка подключения:\n{e}\n\n"
                    f"Проверьте параметры в config.py"
                )
                self.progress.setValue(self._max_attempts)
                self.btnRetry.setEnabled(True)
                self.btnSettings.setEnabled(True)
        else:
            if self._attempt < self._max_attempts:
                # Автоповтор через 2 секунды
                QTimer.singleShot(2000, self._start_check)
            else:
                self.lblStatus.setText(
                    "❌ Сервер MySQL недоступен.\n\n"
                    "Убедитесь, что:\n"
                    "• MySQL запущен\n"
                    "• Параметры в config.py верны\n"
                    "• Сеть доступна"
                )
                self.btnRetry.setEnabled(True)
                self.btnSettings.setEnabled(True)

    def _on_retry(self):
        """Повторить подключение."""
        self._attempt = 0
        self._start_check()

    def _on_settings(self):
        """Открыть config.py в редакторе (опционально)."""
        import subprocess
        import sys
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.py')
        if os.path.exists(config_path):
            if sys.platform == 'win32':
                os.startfile(config_path)
            else:
                subprocess.Popen(['xdg-open', config_path])