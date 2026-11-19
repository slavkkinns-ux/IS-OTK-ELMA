"""Генератор PDF-отчётов для заказов (с поддержкой кириллицы)."""
import os
import sys
from datetime import datetime

from db import order_repo


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

def generate_report_pdf(order_id: int, output_dir: str = "reports") -> str:
    """Генерирует PDF-отчёт для заказа. Возвращает путь к файлу."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    )
    from reportlab.lib import colors

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    order = order_repo.get_order(order_id)
    if not order:
        raise ValueError(f"Заказ #{order_id} не найден")

    services = order_repo.get_order_services(order_id)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"report_{order['vessel_code']}_{timestamp}.pdf"
    filepath = os.path.join(output_dir, filename)

    doc = SimpleDocTemplate(
        filepath, pagesize=A4,
        rightMargin=20 * mm, leftMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontName=FONT_BOLD,
        fontSize=16,
        textColor=colors.HexColor('#174A7E'),
        spaceAfter=12 * mm,
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontName=FONT_BOLD,
        fontSize=12,
        textColor=colors.HexColor('#244B73'),
        spaceAfter=6 * mm,
    )
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontName=FONT_NAME,
        fontSize=10,
    )

    story = []

    # Заголовок
    story.append(Paragraph("ОТЧЁТ ПО ЗАКАЗУ", title_style))
    story.append(Spacer(1, 5 * mm))

    # Информация о заказе
    story.append(Paragraph("Информация о заказе", heading_style))
    order_date_str = ''
    if order.get('order_date'):
        if isinstance(order['order_date'], datetime):
            order_date_str = order['order_date'].strftime('%d.%m.%Y')
        else:
            order_date_str = str(order['order_date'])

    info_data = [
        ['Номер заказа:', str(order['order_id'])],
        ['Код сосуда:', order['vessel_code']],
        ['Клиент:', order['client_name']],
        ['Сотрудник:', order['employee_name']],
        ['Дата:', order_date_str],
        ['Статус:', order['status']],
    ]
    info_table = Table(info_data, colWidths=[50 * mm, 120 * mm])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTNAME', (0, 0), (0, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F0F5FA')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 8 * mm))

    # Услуги
    story.append(Paragraph("Выполненные исследования", heading_style))
    services_data = [['№', 'Услуга', 'Стоимость']]
    total = 0.0
    for idx, s in enumerate(services, 1):
        price = float(s['price'])
        total += price
        services_data.append([
            str(idx),
            s['service_name'],
            f"{price:.2f} ₽",
        ])
    services_data.append(['', 'ИТОГО:', f"{total:.2f} ₽"])

    services_table = Table(services_data, colWidths=[15 * mm, 120 * mm, 35 * mm])
    services_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, -1), FONT_NAME),
        ('FONTNAME', (0, 0), (-1, 0), FONT_BOLD),
        ('FONTNAME', (0, -1), (-1, -1), FONT_BOLD),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#174A7E')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#F0F5FA')),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    story.append(services_table)
    story.append(Spacer(1, 10 * mm))

    # Подпись
    story.append(Paragraph(
        f"Отчёт сформирован: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
        normal_style,
    ))

    doc.build(story)
    return filepath