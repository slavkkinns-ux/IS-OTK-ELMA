"""Диалог подключения к БД."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QObject

from db.connection import check_db, connect, get_config_info, ensure_schema


class _Worker(QObject):
    """Фоновая проверка доступности БД."""
    finished = pyqtSignal(bool, object)

    def check(self):
        ok, err = check_db()
        self.finished.emit(ok, err)


class ConnectionDialog(QDialog):
    """Диалог подключения к БД с автоповтором.
    При успехе закрывается молча. Сообщения — только при ошибках.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к базе данных")
        self.setFixedSize(420, 200)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

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

        self.lblStatus = QLabel("Проверка доступности сервера...")
        self.lblStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblStatus.setWordWrap(True)
        root.addWidget(self.lblStatus)

        self.progress = QProgressBar()
        self.progress.setRange(0, self._max_attempts)
        self.progress.setValue(0)
        root.addWidget(self.progress)

        # Кнопки (по умолчанию скрыты — появляются только при ошибке)
        btns = QHBoxLayout()
        self.btnRetry = QPushButton("Повторить")
        self.btnRetry.clicked.connect(self._on_retry)
        self.btnSettings = QPushButton("Настройки")
        self.btnSettings.clicked.connect(self._on_settings)
        self.btnExit = QPushButton("Выйти")
        self.btnExit.clicked.connect(self.reject)

        btns.addWidget(self.btnRetry)
        btns.addWidget(self.btnSettings)
        btns.addStretch()
        btns.addWidget(self.btnExit)
        root.addLayout(btns)

        # Скрываем кнопки до появления ошибки
        self.btnRetry.setVisible(False)
        self.btnSettings.setVisible(False)
        self.btnExit.setVisible(False)

    def _start_check(self):
        """Запустить проверку в фоне."""
        self._attempt += 1
        self.lblStatus.setText(
            f"Попытка {self._attempt} из {self._max_attempts}...\n"
            f"Проверка доступности сервера MySQL."
        )
        self.progress.setValue(self._attempt - 1)
        self._hide_error_buttons()

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
            # Пытаемся подключиться и проверить структуру
            try:
                connect()
                # Тихая проверка/создание таблиц — без сообщений пользователю
                schema_info = ensure_schema()
                if schema_info.startswith("Созданы таблицы:"):
                    from PyQt6.QtWidgets import QMessageBox
                    QMessageBox.information(
                        self, "Первый запуск",
                        f"Создана структура базы данных:\n{schema_info}\n\n"
                        f"Теперь добавьте сотрудников и услуги через интерфейс приложения."
                    )
                # Короткая пауза, чтобы пользователь увидел "Подключение установлено"
                self.lblStatus.setText("Подключение установлено.")
                self.progress.setValue(self._max_attempts)
                QTimer.singleShot(400, self.accept)
            except Exception as e:
                # Ошибка при подключении или создании таблиц — показываем
                self._show_error(
                    f"Ошибка подключения:\n{e}\n\n"
                    f"Проверьте параметры в config.py"
                )
        else:
            if self._attempt < self._max_attempts:
                # Автоповтор через 2 секунды — без сообщений
                QTimer.singleShot(2000, self._start_check)
            else:
                # Все попытки исчерпаны — показываем ошибку
                self._show_error(
                    "Сервер MySQL недоступен.\n\n"
                    "Убедитесь, что:\n"
                    "• MySQL запущен\n"
                    "• Параметры в config.py верны\n"
                    "• Сеть доступна"
                )

    def _show_error(self, message: str):
        """Показать ошибку и активировать кнопки действий."""
        self.progress.setValue(self._max_attempts)
        self.lblStatus.setText(message)
        self.lblStatus.setStyleSheet("color: #B03A2E;")
        self.btnRetry.setVisible(True)
        self.btnSettings.setVisible(True)
        self.btnExit.setVisible(True)

    def _hide_error_buttons(self):
        """Скрыть кнопки действий (при новой попытке)."""
        self.lblStatus.setStyleSheet("")
        self.btnRetry.setVisible(False)
        self.btnSettings.setVisible(False)
        self.btnExit.setVisible(False)

    def _on_retry(self):
        """Повторить подключение."""
        self._attempt = 0
        self._start_check()

    def _on_settings(self):
        """Открыть config.py в редакторе."""
        import subprocess
        import sys
        import os
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
        if os.path.exists(config_path):
            if sys.platform == 'win32':
                os.startfile(config_path)
            else:
                subprocess.Popen(['xdg-open', config_path])

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        event.accept()