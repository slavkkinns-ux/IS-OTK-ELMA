"""Виджет для отображения логов в UI."""
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt
import logging


class QTextEditLogger(logging.Handler):
    """Логгер, который выводит сообщения в QTextEdit."""
    
    def __init__(self, text_edit: QTextEdit):
        super().__init__()
        self.text_edit = text_edit
    
    def emit(self, record):
        msg = self.format(record)
        self.text_edit.append(msg)


class LogWidget(QWidget):
    """Виджет для просмотра логов."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Логи приложения")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout(self)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Consolas, monospace;
                font-size: 10pt;
            }
        """)
        layout.addWidget(self.text_edit)
        
        btns = QHBoxLayout()
        btn_clear = QPushButton("Очистить")
        btn_clear.clicked.connect(self.text_edit.clear)
        btns.addWidget(btn_clear)
        btns.addStretch()
        layout.addLayout(btns)
        
        # Подключаем логгер
        self.log_handler = QTextEditLogger(self.text_edit)
        self.log_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            datefmt='%H:%M:%S'
        ))
        logging.getLogger("IS_OTK").addHandler(self.log_handler)