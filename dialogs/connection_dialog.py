"""Диалог подключения к БД с формой ввода параметров."""

from __future__ import annotations

import json
import logging
import os

from PyQt6.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from services.connection_service import ConnectionService

logger = logging.getLogger(__name__)


class _Worker(QObject):
    """Фоновая проверка доступности БД."""
    finished = pyqtSignal(bool, str)  # success, error_message

    def __init__(self, connection_service: ConnectionService, parent=None):
        super().__init__(parent)
        self.connection_service = connection_service

    def check(self):
        try:
            result = self.connection_service.is_db_available()
            self.finished.emit(result, "")
        except Exception as e:
            self.finished.emit(False, str(e))


class ConnectionDialog(QDialog):
    """Диалог подключения к базе данных с формой ввода параметров."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Подключение к базе данных")
        self.setFixedSize(480, 520)
        self.setWindowFlags(
            self.windowFlags() & ~Qt.WindowType.WindowCloseButtonHint
        )

        self.connection_service = ConnectionService()
        self._config = self._load_config()

        self._attempt = 0
        self._max_attempts = 5
        self._thread = None
        self._worker = None
        self._auto_retry = True

        self._build_ui()
        self._fill_form()
        self._start_check()

    def _load_config(self) -> dict:
        """Загрузить конфиг из config.json или вернуть дефолты."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_json_path = os.path.join(base_dir, 'config.json')

        defaults = {
            "host": "localhost",
            "port": 3306,
            "user": "root",
            "password": "",
            "database": "elma",
            "charset": "utf8mb4"
        }

        if os.path.exists(config_json_path):
            try:
                with open(config_json_path, encoding='utf-8') as f:
                    data = json.load(f)
                defaults.update(data)
            except Exception:
                pass
        return defaults

    def _save_config(self) -> bool:
        """Сохранить текущий конфиг в config.json."""
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        config_json_path = os.path.join(base_dir, 'config.json')

        try:
            with open(config_json_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=4)
            return True
        except Exception as e:
            logger.error("Failed to save config: %s", e)
            return False

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setSpacing(12)
        root.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        title = QLabel("Настройка подключения к MySQL")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #174A7E;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Введите параметры подключения. Пароль не сохраняется в открытом виде.")
        subtitle.setStyleSheet("color: #666; font-size: 9pt;")
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)

        # Форма ввода
        form_group = QGroupBox("Параметры сервера")
        form_layout = QFormLayout(form_group)
        form_layout.setLabelAlignment(Qt.AlignmentFlag.AlignRight)
        form_layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.ExpandingFieldsGrow)
        form_layout.setSpacing(10)

        self.editHost = QLineEdit()
        self.editHost.setPlaceholderText("localhost")
        form_layout.addRow("Хост:", self.editHost)

        self.editPort = QLineEdit()
        self.editPort.setPlaceholderText("3306")
        self.editPort.setFixedWidth(100)
        form_layout.addRow("Порт:", self.editPort)

        self.editUser = QLineEdit()
        self.editUser.setPlaceholderText("root")
        form_layout.addRow("Пользователь:", self.editUser)

        self.editPassword = QLineEdit()
        self.editPassword.setEchoMode(QLineEdit.EchoMode.Password)
        self.editPassword.setPlaceholderText("Введите пароль")
        form_layout.addRow("Пароль:", self.editPassword)

        self.editDatabase = QLineEdit()
        self.editDatabase.setPlaceholderText("elma")
        form_layout.addRow("База данных:", self.editDatabase)

        self.editCharset = QLineEdit()
        self.editCharset.setPlaceholderText("utf8mb4")
        form_layout.addRow("Кодировка:", self.editCharset)

        root.addWidget(form_group)

        # Статус и прогресс
        self.lblStatus = QLabel("Проверка подключения...")
        self.lblStatus.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lblStatus.setWordWrap(True)
        self.lblStatus.setStyleSheet("color: #333; font-size: 9pt;")
        root.addWidget(self.lblStatus)

        self.progress = QProgressBar()
        self.progress.setRange(0, self._max_attempts)
        self.progress.setValue(0)
        self.progress.setTextVisible(False)
        root.addWidget(self.progress)

        # Кнопки
        btns = QHBoxLayout()
        btns.setSpacing(10)

        self.btnTest = QPushButton("🔍 Проверить")
        self.btnTest.setFixedHeight(36)
        self.btnTest.clicked.connect(self._on_test)
        btns.addWidget(self.btnTest)

        self.btnConnect = QPushButton("💾 Сохранить и подключиться")
        self.btnConnect.setFixedHeight(36)
        self.btnConnect.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                font-weight: bold;
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #219653; }
            QPushButton:pressed { background-color: #1E8449; }
        """)
        self.btnConnect.clicked.connect(self._on_connect)
        btns.addWidget(self.btnConnect)

        self.btnExit = QPushButton("✕ Выйти")
        self.btnExit.setFixedHeight(36)
        self.btnExit.setStyleSheet("""
            QPushButton { color: #E74C3C; font-weight: bold; border-radius: 4px; }
            QPushButton:hover { background-color: #FADBD8; }
        """)
        self.btnExit.clicked.connect(self.reject)
        btns.addWidget(self.btnExit)

        root.addLayout(btns)

        # Изначально кнопки проверки/подключения активны
        self._set_controls_enabled(True)

    def _fill_form(self):
        """Заполнить форму значениями из конфига."""
        self.editHost.setText(self._config.get("host", "localhost"))
        self.editPort.setText(str(self._config.get("port", 3306)))
        self.editUser.setText(self._config.get("user", "root"))
        self.editPassword.setText(self._config.get("password", ""))
        self.editDatabase.setText(self._config.get("database", "elma"))
        self.editCharset.setText(self._config.get("charset", "utf8mb4"))

    def _read_form(self) -> dict:
        """Прочитать значения из формы."""
        return {
            "host": self.editHost.text().strip() or "localhost",
            "port": int(self.editPort.text().strip() or 3306),
            "user": self.editUser.text().strip() or "root",
            "password": self.editPassword.text(),  # пароль может быть пустым
            "database": self.editDatabase.text().strip() or "elma",
            "charset": self.editCharset.text().strip() or "utf8mb4"
        }

    def _apply_config(self, config: dict):
        """Применить конфиг к connection_service (перезагрузить конфиг в db.connection)."""
        self._config = config
        # Принудительно перезагрузить конфиг в db.connection
        from db import connection as db_conn
        db_conn._config = None  # сброс кэша
        # Обновить connection_service (он использует db.connection внутри)
        self.connection_service = ConnectionService()

    def _set_controls_enabled(self, enabled: bool):
        self.editHost.setEnabled(enabled)
        self.editPort.setEnabled(enabled)
        self.editUser.setEnabled(enabled)
        self.editPassword.setEnabled(enabled)
        self.editDatabase.setEnabled(enabled)
        self.editCharset.setEnabled(enabled)
        self.btnTest.setEnabled(enabled)
        self.btnConnect.setEnabled(enabled)

    def _on_test(self):
        """Проверить подключение с текущими параметрами формы."""
        config = self._read_form()
        self._apply_config(config)

        self._set_controls_enabled(False)
        self.lblStatus.setText("Проверка подключения...")
        self.lblStatus.setStyleSheet("color: #333;")
        self.progress.setValue(0)

        self._attempt = 0
        self._auto_retry = False  # при ручной проверке не авто-ретраим
        self._start_check()

    def _on_connect(self):
        """Сохранить конфиг и подключиться."""
        config = self._read_form()

        if not config["password"]:
            QMessageBox.warning(self, "Пароль", "Введите пароль для подключения к MySQL.")
            return

        self._apply_config(config)

        if not self._save_config():
            QMessageBox.critical(self, "Ошибка", "Не удалось сохранить config.json")
            return

        self._set_controls_enabled(False)
        self.lblStatus.setText("Подключение и миграция БД...")
        self.lblStatus.setStyleSheet("color: #333;")
        self.progress.setValue(0)

        self._attempt = 0
        self._auto_retry = True
        self._start_check()

    def _start_check(self):
        """Запустить проверку в фоне."""
        self._attempt += 1
        self.lblStatus.setText(
            f"Попытка {self._attempt} из {self._max_attempts}...\n"
            f"Проверка доступности сервера MySQL."
        )
        self.progress.setValue(self._attempt - 1)

        self._thread = QThread(self)
        self._worker = _Worker(self.connection_service)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.check)
        self._worker.finished.connect(self._on_check_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_check_finished(self, available: bool, error_msg: str):
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
                    self.lblStatus.setStyleSheet("color: #B03A2E;")
                    self._set_controls_enabled(True)
                    return

                QTimer.singleShot(400, self.accept)
            except Exception as e:
                self._show_error(f"Ошибка подключения:\n{e}")
        else:
            if self._auto_retry and self._attempt < self._max_attempts:
                QTimer.singleShot(2000, self._start_check)
            else:
                msg = "Сервер MySQL недоступен.\n\n"
                if error_msg:
                    msg += f"Ошибка: {error_msg}\n\n"
                msg += "Проверьте:\n• MySQL запущен\n• Хост, порт, пользователь верны\n• Сеть доступна"
                self._show_error(msg)

    def _show_error(self, message: str):
        self.progress.setValue(self._max_attempts)
        self.lblStatus.setText(message)
        self.lblStatus.setStyleSheet("color: #B03A2E;")
        self._set_controls_enabled(True)

    def closeEvent(self, event):
        if self._thread and self._thread.isRunning():
            self._thread.quit()
            self._thread.wait(2000)
        event.accept()


__all__ = ["ConnectionDialog"]