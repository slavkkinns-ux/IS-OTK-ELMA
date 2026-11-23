"""Единые QSS-стили приложения (устранение дублирования в диалогах и окнах)."""

from __future__ import annotations


def button_style(bg: str, hover: str, padding: str = "8px 16px", radius: int = 6) -> str:
    """Собрать QSS для цветной кнопки."""
    return f"""
        QPushButton {{
            background-color: {bg};
            color: white;
            border: none;
            padding: {padding};
            border-radius: {radius}px;
            font-weight: bold;
        }}
        QPushButton:hover {{ background-color: {hover}; }}
        QPushButton:disabled {{ background-color: #BDC3C7; color: #7F8C8D; }}
    """


PRIMARY_BUTTON_STYLE = button_style("#2D83D5", "#3B94E8")
SUCCESS_BUTTON_STYLE = button_style("#27AE60", "#2ECC71")
DANGER_BUTTON_STYLE = button_style("#E74C3C", "#C0392B")
WARNING_BUTTON_STYLE = button_style("#F39C12", "#E67E22")

TITLE_STYLE = "font-size: 14pt; font-weight: bold; color: #174A7E; padding: 5px;"
TOTAL_VALUE_STYLE = "font-size: 14pt; font-weight: bold; color: #174A7E;"
HINT_STYLE = "color: #666; font-size: 9pt;"

TABLE_STYLE = """
    QHeaderView::section {
        background-color: #174A7E; color: white; font-weight: bold;
        padding: 5px; border: 1px solid #CBD7E4;
    }
    QTableWidget {
        border: 1px solid #CBD7E4; gridline-color: #CBD7E4;
    }
"""

TABLE_CARD_STYLE = """
    QTableWidget {
        background-color: #FFFFFF;
        border: 1px solid #D8E3EF;
        border-radius: 8px;
        gridline-color: #D8E3EF;
        font-size: 10pt;
    }
    QTableWidget::item { padding: 8px; }
    QHeaderView::section {
        background-color: #174A7E;
        color: white;
        padding: 10px;
        border: none;
        font-weight: bold;
        font-size: 10pt;
    }
"""

GROUPBOX_TITLED_STYLE = """
    QGroupBox {
        font-weight: bold;
        font-size: 11pt;
        border: 1px solid #CBD7E4;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px;
    }
"""

INFO_PANEL_STYLE = """
    QLabel {
        background-color: #F0F5FA;
        border: 1px solid #D8E3EF;
        border-radius: 6px;
        padding: 10px;
        font-size: 9pt;
    }
"""

STAT_CARD_STYLE = """
    QGroupBox {
        background-color: #F0F5FA;
        border: 2px solid #174A7E;
        border-radius: 8px;
        padding: 15px;
    }
"""

ROLE_COLORS: dict[str, str] = {
    "admin": "#C0392B",
    "controller": "#2980B9",
    "lab_technician": "#27AE60",
    "manager": "#F39C12",
}
DEFAULT_ROLE_COLOR = "#95A5A6"

# Sidebar кнопки — адаптивные стили без фиксированной ширины
SIDEBAR_BUTTON_STYLE = """
    QPushButton {
        background-color: transparent;
        color: #ECF0F1;
        border: none;
        padding: 10px 12px;
        border-radius: 6px;
        font-size: 10pt;
        font-weight: bold;
        text-align: left;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #1A5A8A;
    }
    QPushButton:checked {
        background-color: #154360;
        border-left: 3px solid #3498DB;
        padding-left: 10px;
    }
    QPushButton:pressed {
        background-color: #1A5A8A;
    }
"""

SIDEBAR_BUTTON_SECONDARY_STYLE = """
    QPushButton {
        background-color: #2C3E50;
        color: white;
        border: none;
        padding: 10px 12px;
        border-radius: 6px;
        font-size: 10pt;
        font-weight: bold;
        text-align: left;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #34495E;
    }
    QPushButton:pressed {
        background-color: #1A252F;
    }
"""

SIDEBAR_DANGER_BUTTON_STYLE = """
    QPushButton {
        background-color: #2C3E50;
        color: #E74C3C;
        border: none;
        padding: 10px 12px;
        border-radius: 6px;
        font-size: 10pt;
        font-weight: bold;
        text-align: left;
        min-height: 32px;
    }
    QPushButton:hover {
        background-color: #34495E;
        color: #FF6B6B;
    }
    QPushButton:pressed {
        background-color: #1A252F;
    }
"""
