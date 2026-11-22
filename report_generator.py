"""Генератор PDF-отчётов для заказов (с поддержкой кириллицы)."""
import os
import sys
from datetime import datetime
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from db import order_repo, report_repo

# =============================================================================
# Регистрация кириллического шрифта
# =============================================================================
def _register_cyrillic_font():
    """Регистрирует шрифт Arial (или DejaVu) для поддержки кириллицы."""
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    candidates = []
    if sys.platform == 'win32':
        candidates = [
            (r'C:\Windows\Fonts\arial.ttf', 'Arial'),
            (r'C:\Windows\Fonts\arialbd.ttf', 'Arial-Bold'),
        ]
    elif sys.platform == 'darwin':
        candidates = [
            ('/Library/Fonts/Arial.ttf', 'Arial'),
            ('/Library/Fonts/Arial Bold.ttf', 'Arial-Bold'),
        ]
    else:  # Linux
        candidates = [
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 'Arial'),
            ('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 'Arial-Bold'),
        ]

    for path, name in candidates:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:
                pass

# Регистрируем один раз при импорте
_register_cyrillic_font()

# Имена зарегистрированных шрифтов (фоллбэк на Helvetica, если Arial не найден)
FONT_NAME = 'Arial'
FONT_BOLD = 'Arial-Bold'


def _font_available(name: str) -> bool:
    from reportlab.pdfbase import pdfmetrics
    try:
        pdfmetrics.getFont(name)
        return True
    except KeyError:
        return False


if not _font_available(FONT_NAME):
    FONT_NAME = 'Helvetica'
    FONT_BOLD = 'Helvetica-Bold'


# =============================================================================
# Генерация PDF
# =============================================================================
def generate_report_pdf(order_id: int, report_id: int = None) -> str:
    """Сгенерировать PDF отчёта.

    Args:
        order_id: ID заказа
        report_id: ID отчёта (для имени файла). Если None, используется order_id.
    """
    # Путь к папке reports
    reports_dir = Path(__file__).parent / 'reports'
    reports_dir.mkdir(exist_ok=True)

    # Формируем имя файла
    if report_id:
        filename = f"ОТЧ-{report_id:04d}.pdf"
    else:
        filename = f"ОТЧ-{order_id:04d}.pdf"

    filepath = str(reports_dir / filename)

    # Получаем данные заказа
    order = order_repo.get_order(order_id)
    if not order:
        raise ValueError(f"Заказ {order_id} не найден")

    # Получаем исследования по заказу
    research_rows = report_repo.get_report_research(order_id)

    # Создаём PDF
    c = canvas.Canvas(filepath, pagesize=A4)
    width, height = A4

    y = height - 30  # начальная позиция Y (сверху)

    # --- Шапка ---
    c.setFont(FONT_BOLD, 14)
    c.drawCentredString(width / 2, y, 'ООО "СПбЦ "ЭЛМА""')
    y -= 40

    c.setFont(FONT_BOLD, 12)
    c.setFillColor(colors.HexColor('#174A7E'))
    c.drawCentredString(width / 2, y, 'ОТЧЁТ О РЕЗУЛЬТАТАХ ИССЛЕДОВАНИЙ')
    c.setFillColor(colors.black)
    y -= 40

    # --- Реквизиты ---
    c.setFont(FONT_NAME, 10)
    report_num = f"ОТЧ-{report_id:04d}" if report_id else f"ОТЧ-{order_id:04d}"
    report_date = datetime.now().strftime('%d.%m.%Y')
    c.drawString(30, y, f"Номер отчёта: {report_num} от {report_date}")
    y -= 20

    client_name = order.get('client_name', '')
    c.drawString(30, y, f"Заказчик: {client_name}")
    y -= 20

    vessel_code = order.get('vessel_code', '')
    order_date = order.get('order_date')
    if order_date:
        if hasattr(order_date, 'strftime'):
            order_date_str = order_date.strftime('%d.%m.%Y')
        else:
            order_date_str = str(order_date)
    else:
        order_date_str = ''

    # ИСПРАВЛЕНО: vessel_code вместо order_id
    c.drawString(30, y, f"Номер заказа: {vessel_code}    Дата: {order_date_str}")
    y -= 40

    # --- Заголовок таблицы ---
    c.setFont(FONT_BOLD, 11)
    c.setFillColor(colors.HexColor('#174A7E'))
    c.drawCentredString(width / 2, y, 'Перечень выполненных исследований:')
    c.setFillColor(colors.black)
    y -= 25

    # --- Таблица исследований ---
    if research_rows:
        # Заголовки
        table_data = [['№', 'Исследование', 'Результат', 'Заключение']]

        for idx, row in enumerate(research_rows, 1):
            service_name = row.get('service_name', '') or ''
            result_value = row.get('result_value', '') or 'Не выполнено'
            conclusion = row.get('conclusion', '') or '-'
            table_data.append([str(idx), service_name, result_value, conclusion])

        # Создаём стили для ячеек с кириллицей
        header_style = ParagraphStyle(
            'HeaderStyle',
            fontName=FONT_BOLD,
            fontSize=9,
            textColor=colors.white,
            alignment=TA_CENTER,
            leading=11,
        )
        cell_style = ParagraphStyle(
            'CellStyle',
            fontName=FONT_NAME,
            fontSize=9,
            leading=11,
        )
        cell_style_center = ParagraphStyle(
            'CellStyleCenter',
            fontName=FONT_NAME,
            fontSize=9,
            alignment=TA_CENTER,
            leading=11,
        )

        # Формируем данные таблицы с Paragraph (для переноса текста)
        styled_data = []
        for row_idx, row in enumerate(table_data):
            if row_idx == 0:
                styled_row = [
                    Paragraph(row[0], header_style),
                    Paragraph(row[1], header_style),
                    Paragraph(row[2], header_style),
                    Paragraph(row[3], header_style),
                ]
            else:
                styled_row = [
                    Paragraph(row[0], cell_style_center),
                    Paragraph(row[1], cell_style),
                    Paragraph(row[2], cell_style),
                    Paragraph(row[3], cell_style),
                ]
            styled_data.append(styled_row)

        # Ширина колонок: № узкая, Исследование широкая, Результат и Заключение средние
        col_widths = [30, 220, 130, 130]
        table = Table(styled_data, colWidths=col_widths, repeatRows=1)

        table.setStyle(TableStyle([
            # Шапка
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#174A7E')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            # Сетка
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D2DFEC')),
            # Выравнивание
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            # Чередование строк
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F5FA')]),
        ]))

        # Рисуем таблицу
        table.wrapOn(c, width - 60, height)
        table_height = table._height
        table.drawOn(c, 30, y - table_height)
        y -= table_height + 30
    else:
        c.setFont(FONT_NAME, 10)
        c.drawString(30, y, 'Исследования не назначены')
        y -= 30

    # --- Заключение ---
    c.setFont(FONT_NAME, 10)
    conclusions = [r.get('conclusion') for r in research_rows if r.get('conclusion')]
    if conclusions:
        conclusion_text = "Заключение: " + "; ".join(conclusions)
    elif research_rows and all(r.get('result_value') for r in research_rows):
        conclusion_text = "Заключение: все исследования выполнены."
    else:
        conclusion_text = "Заключение: часть исследований ещё не выполнена."

    # Разбиваем длинный текст на строки
    max_line_length = 90
    lines = [conclusion_text[i:i + max_line_length]
             for i in range(0, len(conclusion_text), max_line_length)]
    for line in lines:
        c.drawString(30, y, line)
        y -= 15

    c.save()
    return filepath