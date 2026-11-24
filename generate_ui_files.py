#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Generate .ui files from existing pyuic6-style UI classes.
This script loads each UI class, creates the widgets, and writes a .ui file
that matches the original Qt Designer output as closely as possible.
"""

import sys
import os

os.environ['QT_QPA_PLATFORMTHEME'] = ''

from PyQt6.QtWidgets import (
    QApplication, QWidget, QBoxLayout, QComboBox, QAbstractSpinBox,
    QAbstractSlider, QSizePolicy, QFrame, QLabel, QPushButton, QLineEdit,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QDateEdit, QSpinBox, QDoubleSpinBox, QDateTimeEdit, QTimeEdit,
    QScrollArea, QTextEdit, QPlainTextEdit, QCheckBox, QRadioButton,
    QGroupBox, QTabWidget, QListWidget, QTreeWidget, QSlider, QProgressBar,
    QDial, QLCDNumber, QSplitter, QStackedWidget, QToolButton, QMenuBar,
    QStatusBar, QToolBar, QDockWidget, QMainWindow
)
from PyQt6.QtCore import (
    QFile, QIODevice, QXmlStreamWriter, Qt, QRect, QSize, QPoint,
    QMetaProperty, QMetaObject, QMetaMethod
)
from PyQt6.QtGui import QFont, QCursor

# Import all UI classes
from ui.pages import (
    Ui_HomePage, Ui_OrdersPage, Ui_ClientsPage,
    Ui_ResearchPage, Ui_ReportsPage, Ui_EmployeesPage
)


app = QApplication(sys.argv)

# Widgets to skip (internal Qt widgets)
SKIP_WIDGETS = {
    'QComboBoxPrivateContainer', 'QComboBoxListView', 'QMenu', 'QToolTip',
    'QAbstractItemView', 'QListView', 'QTableView', 'QTreeView',
    'QHeaderView', 'QScrollBar', 'QAbstractScrollArea',
    'QLineEditIconButton', 'QWidgetLineControl', 'QWidgetTextControl',
}

# Parent classes whose unnamed children should be skipped
INTERNAL_PARENTS = {
    'QComboBox', 'QSpinBox', 'QDoubleSpinBox', 'QDateTimeEdit',
    'QDateEdit', 'QTimeEdit', 'QScrollArea', 'QAbstractItemView',
    'QTableWidget', 'QLineEdit', 'QTextEdit', 'QPlainTextEdit',
    'QComboBoxPrivateContainer', 'QAbstractSpinBox',
}


def is_internal_widget(widget):
    """Check if widget is an internal Qt widget that shouldn't be in .ui"""
    class_name = widget.metaObject().className()
    if class_name in SKIP_WIDGETS:
        return True
    obj_name = widget.objectName()
    if obj_name.startswith('qt_'):
        return True
    if not obj_name and class_name.startswith('Q'):
        parent = widget.parent()
        if parent:
            parent_class = parent.metaObject().className()
            if parent_class in INTERNAL_PARENTS:
                return True
    return False


def write_layout(layout, writer):
    """Write a layout element with all its properties and items"""
    layout_class = layout.metaObject().className()
    writer.writeStartElement('layout')
    writer.writeAttribute('class', layout_class)
    writer.writeAttribute('name', layout.objectName() or layout_class.lower())

    # Layout margins
    margins = layout.contentsMargins()
    for margin_name, margin_val in [
        ('leftMargin', margins.left()), ('topMargin', margins.top()),
        ('rightMargin', margins.right()), ('bottomMargin', margins.bottom())
    ]:
        if margin_val > 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', margin_name)
            writer.writeStartElement('number')
            writer.writeCharacters(str(margin_val))
            writer.writeEndElement()
            writer.writeEndElement()

    # Layout spacing
    if layout.spacing() >= 0:
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'spacing')
        writer.writeStartElement('number')
        writer.writeCharacters(str(layout.spacing()))
        writer.writeEndElement()
        writer.writeEndElement()

    # Size constraint (always write default)
    writer.writeStartElement('property')
    writer.writeAttribute('name', 'sizeConstraint')
    writer.writeStartElement('enum')
    writer.writeCharacters('QLayout::SetDefaultConstraint')
    writer.writeEndElement()
    writer.writeEndElement()

    # Layout items
    for i in range(layout.count()):
        item = layout.itemAt(i)
        if not item:
            continue
        writer.writeStartElement('item')
        if hasattr(item, 'alignment') and item.alignment():
            writer.writeAttribute('alignment', str(int(item.alignment())))

        child_widget = item.widget()
        child_layout = item.layout()
        spacer = item.spacerItem()

        if child_widget:
            if not is_internal_widget(child_widget):
                write_widget_in_layout(child_widget, writer)
        elif child_layout:
            write_layout(child_layout, writer)
        elif spacer:
            write_spacer(writer, layout, i)
        else:
            write_spacer(writer, layout, i)

        writer.writeEndElement()  # item

    writer.writeEndElement()  # layout


def write_spacer(writer, layout, index):
    """Write a spacer item in Qt4/Qt5 format"""
    writer.writeStartElement('spacer')
    writer.writeAttribute('name', f'spacer_{index}')

    writer.writeStartElement('property')
    writer.writeAttribute('name', 'orientation')
    writer.writeStartElement('enum')
    if isinstance(layout, QBoxLayout):
        if layout.direction() in [QBoxLayout.Direction.TopToBottom, QBoxLayout.Direction.BottomToTop]:
            writer.writeCharacters('Qt::Vertical')
        else:
            writer.writeCharacters('Qt::Horizontal')
    else:
        writer.writeCharacters('Qt::Vertical')
    writer.writeEndElement()
    writer.writeEndElement()

    writer.writeStartElement('property')
    writer.writeAttribute('name', 'sizeType')
    writer.writeStartElement('enum')
    writer.writeCharacters('QSizePolicy::Expanding')
    writer.writeEndElement()
    writer.writeEndElement()

    writer.writeStartElement('property')
    writer.writeAttribute('name', 'sizeHint')
    writer.writeAttribute('stdset', '0')
    writer.writeStartElement('size')
    writer.writeTextElement('width', '20')
    writer.writeTextElement('height', '20')
    writer.writeEndElement()
    writer.writeEndElement()

    writer.writeEndElement()  # spacer


def write_font_properties(font, writer):
    """Write font properties if they differ from defaults"""
    if font.pointSize() > 0:
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'font')
        writer.writeStartElement('font')
        writer.writeStartElement('pointsize')
        writer.writeCharacters(str(font.pointSize()))
        writer.writeEndElement()
        if font.bold():
            writer.writeStartElement('weight')
            writer.writeCharacters('75')
            writer.writeEndElement()
        if font.italic():
            writer.writeStartElement('italic')
            writer.writeCharacters('true')
            writer.writeEndElement()
        if font.underline():
            writer.writeStartElement('underline')
            writer.writeCharacters('true')
            writer.writeEndElement()
        if font.strikeOut():
            writer.writeStartElement('strikeout')
            writer.writeCharacters('true')
            writer.writeEndElement()
        writer.writeEndElement()  # font
        writer.writeEndElement()  # property


def write_cursor_property(widget, writer):
    """Write cursor property if not default"""
    cursor = widget.cursor()
    if cursor.shape() != Qt.CursorShape.ArrowCursor:
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'cursor')
        writer.writeStartElement('cursorShape')
        # Map cursor shapes to cursorShape names (without Qt:: prefix)
        cursor_map = {
            Qt.CursorShape.ArrowCursor: 'ArrowCursor',
            Qt.CursorShape.UpArrowCursor: 'UpArrowCursor',
            Qt.CursorShape.CrossCursor: 'CrossCursor',
            Qt.CursorShape.WaitCursor: 'WaitCursor',
            Qt.CursorShape.IBeamCursor: 'IBeamCursor',
            Qt.CursorShape.SizeVerCursor: 'SizeVerCursor',
            Qt.CursorShape.SizeHorCursor: 'SizeHorCursor',
            Qt.CursorShape.SizeBDiagCursor: 'SizeBDiagCursor',
            Qt.CursorShape.SizeFDiagCursor: 'SizeFDiagCursor',
            Qt.CursorShape.SizeAllCursor: 'SizeAllCursor',
            Qt.CursorShape.BlankCursor: 'BlankCursor',
            Qt.CursorShape.SplitVCursor: 'SplitVCursor',
            Qt.CursorShape.SplitHCursor: 'SplitHCursor',
            Qt.CursorShape.PointingHandCursor: 'PointingHandCursor',
            Qt.CursorShape.ForbiddenCursor: 'ForbiddenCursor',
            Qt.CursorShape.WhatsThisCursor: 'WhatsThisCursor',
            Qt.CursorShape.BusyCursor: 'BusyCursor',
            Qt.CursorShape.OpenHandCursor: 'OpenHandCursor',
            Qt.CursorShape.ClosedHandCursor: 'ClosedHandCursor',
            Qt.CursorShape.DragCopyCursor: 'DragCopyCursor',
            Qt.CursorShape.DragMoveCursor: 'DragMoveCursor',
            Qt.CursorShape.DragLinkCursor: 'DragLinkCursor',
        }
        writer.writeCharacters(cursor_map.get(cursor.shape(), 'ArrowCursor'))
        writer.writeEndElement()
        writer.writeEndElement()


def write_size_policy(widget, writer):
    """Write sizePolicy property"""
    policy = widget.sizePolicy()
    h_type_map = {
        QSizePolicy.Policy.Fixed: 'Fixed',
        QSizePolicy.Policy.Minimum: 'Minimum',
        QSizePolicy.Policy.Maximum: 'Maximum',
        QSizePolicy.Policy.Preferred: 'Preferred',
        QSizePolicy.Policy.Expanding: 'Expanding',
        QSizePolicy.Policy.MinimumExpanding: 'MinimumExpanding',
        QSizePolicy.Policy.Ignored: 'Ignored',
    }
    v_type_map = {
        QSizePolicy.Policy.Fixed: 'Fixed',
        QSizePolicy.Policy.Minimum: 'Minimum',
        QSizePolicy.Policy.Maximum: 'Maximum',
        QSizePolicy.Policy.Preferred: 'Preferred',
        QSizePolicy.Policy.Expanding: 'Expanding',
        QSizePolicy.Policy.MinimumExpanding: 'MinimumExpanding',
        QSizePolicy.Policy.Ignored: 'Ignored',
    }
    hsizetype = h_type_map.get(policy.horizontalPolicy(), 'Preferred')
    vsizetype = v_type_map.get(policy.verticalPolicy(), 'Preferred')
    
    writer.writeStartElement('property')
    writer.writeAttribute('name', 'sizePolicy')
    writer.writeStartElement('sizepolicy')
    writer.writeAttribute('hsizetype', hsizetype)
    writer.writeAttribute('vsizetype', vsizetype)
    writer.writeStartElement('horstretch')
    writer.writeCharacters('0')
    writer.writeEndElement()
    writer.writeStartElement('verstretch')
    writer.writeCharacters('0')
    writer.writeEndElement()
    writer.writeEndElement()  # sizepolicy
    writer.writeEndElement()  # property


def write_min_max_size(widget, writer):
    """Write minimumSize and maximumSize properties"""
    min_size = widget.minimumSize()
    if min_size.width() > 0 or min_size.height() > 0:
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'minimumSize')
        writer.writeStartElement('size')
        writer.writeTextElement('width', str(min_size.width()))
        writer.writeTextElement('height', str(min_size.height()))
        writer.writeEndElement()
        writer.writeEndElement()

    max_size = widget.maximumSize()
    # Only write if not the default max (16777215, 16777215)
    if max_size.width() < 16777215 or max_size.height() < 16777215:
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'maximumSize')
        writer.writeStartElement('size')
        writer.writeTextElement('width', str(max_size.width()))
        writer.writeTextElement('height', str(max_size.height()))
        writer.writeEndElement()
        writer.writeEndElement()


def write_alignment(widget, writer):
    """Write alignment property for labels and similar"""
    if hasattr(widget, 'alignment'):
        align = widget.alignment()
        if align:
            # Build the alignment string like Qt does
            align_parts = []
            if align & Qt.AlignmentFlag.AlignLeft:
                align_parts.append('Qt::AlignLeft')
            if align & Qt.AlignmentFlag.AlignRight:
                align_parts.append('Qt::AlignRight')
            if align & Qt.AlignmentFlag.AlignHCenter:
                align_parts.append('Qt::AlignHCenter')
            if align & Qt.AlignmentFlag.AlignJustify:
                align_parts.append('Qt::AlignJustify')
            if align & Qt.AlignmentFlag.AlignTop:
                align_parts.append('Qt::AlignTop')
            if align & Qt.AlignmentFlag.AlignBottom:
                align_parts.append('Qt::AlignBottom')
            if align & Qt.AlignmentFlag.AlignVCenter:
                align_parts.append('Qt::AlignVCenter')
            if align & Qt.AlignmentFlag.AlignBaseline:
                align_parts.append('Qt::AlignBaseline')
            if align & Qt.AlignmentFlag.AlignAbsolute:
                align_parts.append('Qt::AlignAbsolute')
            if align & Qt.AlignmentFlag.AlignLeading:
                align_parts.append('Qt::AlignLeading')
            if align & Qt.AlignmentFlag.AlignTrailing:
                align_parts.append('Qt::AlignTrailing')
            
            if align_parts:
                writer.writeStartElement('property')
                writer.writeAttribute('name', 'alignment')
                writer.writeStartElement('set')
                writer.writeCharacters('|'.join(align_parts))
                writer.writeEndElement()  # set
                writer.writeEndElement()  # property


def write_word_wrap(widget, writer):
    """Write wordWrap property"""
    if hasattr(widget, 'wordWrap') and callable(getattr(widget, 'wordWrap')):
        if widget.wordWrap():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'wordWrap')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()


def write_frame_properties(widget, writer):
    """Write frameShape, frameShadow, lineWidth for QFrame"""
    if isinstance(widget, QFrame):
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'frameShape')
        writer.writeStartElement('enum')
        shape_map = {
            QFrame.Shape.NoFrame: 'QFrame::NoFrame',
            QFrame.Shape.Box: 'QFrame::Box',
            QFrame.Shape.Panel: 'QFrame::Panel',
            QFrame.Shape.StyledPanel: 'QFrame::StyledPanel',
            QFrame.Shape.HLine: 'QFrame::HLine',
            QFrame.Shape.VLine: 'QFrame::VLine',
            QFrame.Shape.WinPanel: 'QFrame::WinPanel',
        }
        writer.writeCharacters(shape_map.get(widget.frameShape(), 'QFrame::NoFrame'))
        writer.writeEndElement()
        writer.writeEndElement()

        writer.writeStartElement('property')
        writer.writeAttribute('name', 'frameShadow')
        writer.writeStartElement('enum')
        shadow_map = {
            QFrame.Shadow.Plain: 'QFrame::Plain',
            QFrame.Shadow.Raised: 'QFrame::Raised',
            QFrame.Shadow.Sunken: 'QFrame::Sunken',
        }
        writer.writeCharacters(shadow_map.get(widget.frameShadow(), 'QFrame::Raised'))
        writer.writeEndElement()
        writer.writeEndElement()

        if widget.lineWidth() != 1:  # default is 1
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'lineWidth')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.lineWidth()))
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.midLineWidth() != 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'midLineWidth')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.midLineWidth()))
            writer.writeEndElement()
            writer.writeEndElement()


def write_table_properties(widget, writer):
    """Write QTableWidget specific properties"""
    if isinstance(widget, QTableWidget):
        # editTriggers
        if widget.editTriggers() != QAbstractItemView.EditTrigger.NoEditTriggers:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'editTriggers')
            writer.writeStartElement('set')
            triggers_map = {
                QAbstractItemView.EditTrigger.NoEditTriggers: 'QAbstractItemView::NoEditTriggers',
                QAbstractItemView.EditTrigger.CurrentChanged: 'QAbstractItemView::CurrentChanged',
                QAbstractItemView.EditTrigger.DoubleClicked: 'QAbstractItemView::DoubleClicked',
                QAbstractItemView.EditTrigger.SelectedClicked: 'QAbstractItemView::SelectedClicked',
                QAbstractItemView.EditTrigger.EditKeyPressed: 'QAbstractItemView::EditKeyPressed',
                QAbstractItemView.EditTrigger.AnyKeyPressed: 'QAbstractItemView::AnyKeyPressed',
                QAbstractItemView.EditTrigger.AllEditTriggers: 'QAbstractItemView::AllEditTriggers',
            }
            for trigger, name in triggers_map.items():
                if widget.editTriggers() & trigger:
                    writer.writeStartElement('enum')
                    writer.writeCharacters(name)
                    writer.writeEndElement()
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.alternatingRowColors():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'alternatingRowColors')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.selectionBehavior() != QAbstractItemView.SelectionBehavior.SelectItems:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'selectionBehavior')
            writer.writeStartElement('enum')
            sel_map = {
                QAbstractItemView.SelectionBehavior.SelectItems: 'QAbstractItemView::SelectItems',
                QAbstractItemView.SelectionBehavior.SelectRows: 'QAbstractItemView::SelectRows',
                QAbstractItemView.SelectionBehavior.SelectColumns: 'QAbstractItemView::SelectColumns',
            }
            writer.writeCharacters(sel_map.get(widget.selectionBehavior(), 'QAbstractItemView::SelectItems'))
            writer.writeEndElement()
            writer.writeEndElement()

        if not widget.showGrid():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'showGrid')
            writer.writeStartElement('bool')
            writer.writeCharacters('false')
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.wordWrap():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'wordWrap')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()

        # columnCount and rowCount
        if widget.columnCount() > 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'columnCount')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.columnCount()))
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.rowCount() > 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'rowCount')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.rowCount()))
            writer.writeEndElement()
            writer.writeEndElement()

        # Horizontal header items with text - SKIPPED because PyQt6 uic doesn't support this format
        # Header texts should be set in Python code via retranslateUi or setupUi
        # for col in range(widget.columnCount()):
        #     item = widget.horizontalHeaderItem(col)
        #     if item and item.text():
        #         writer.writeStartElement('property')
        #         writer.writeAttribute('name', f'horizontalHeaderItem_{col}')
        #         writer.writeStartElement('item')
        #         writer.writeAttribute('row', '0')
        #         writer.writeAttribute('column', str(col))
        #         writer.writeStartElement('property')
        #         writer.writeAttribute('name', 'text')
        #         writer.writeStartElement('string')
        #         writer.writeAttribute('notr', 'true')
        #         writer.writeCharacters(item.text())
        #         writer.writeEndElement()
        #         writer.writeEndElement()
        #         writer.writeEndElement()  # item
        #         writer.writeEndElement()  # property

        # Vertical header default section size - SKIPPED
        # vheader = widget.verticalHeader()
        # if vheader and vheader.defaultSectionSize() != 25:  # default
        #     writer.writeStartElement('property')
        #     writer.writeAttribute('name', 'verticalHeaderDefaultSectionSize')
        #     writer.writeStartElement('number')
        #     writer.writeCharacters(str(vheader.defaultSectionSize()))
        #     writer.writeEndElement()
        #     writer.writeEndElement()


def write_combo_box_properties(widget, writer):
    """Write QComboBox specific properties"""
    if isinstance(widget, QComboBox):
        if widget.isEditable():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'editable')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.count() > 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'currentIndex')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.currentIndex()))
            writer.writeEndElement()
            writer.writeEndElement()


def write_date_edit_properties(widget, writer):
    """Write QDateEdit/QDateTimeEdit/QTimeEdit specific properties"""
    if isinstance(widget, (QDateEdit, QDateTimeEdit, QTimeEdit)):
        # date/time
        if isinstance(widget, QDateEdit):
            date = widget.date()
            if date.isValid():
                writer.writeStartElement('property')
                writer.writeAttribute('name', 'date')
                writer.writeStartElement('date')
                writer.writeCharacters(date.toString(Qt.DateFormat.ISODate))
                writer.writeEndElement()
                writer.writeEndElement()
        elif isinstance(widget, QTimeEdit):
            time = widget.time()
            if time.isValid():
                writer.writeStartElement('property')
                writer.writeAttribute('name', 'time')
                writer.writeStartElement('time')
                writer.writeCharacters(time.toString(Qt.DateFormat.ISODate))
                writer.writeEndElement()
                writer.writeEndElement()
        elif isinstance(widget, QDateTimeEdit):
            dt = widget.dateTime()
            if dt.isValid():
                writer.writeStartElement('property')
                writer.writeAttribute('name', 'dateTime')
                writer.writeStartElement('datetime')
                writer.writeCharacters(dt.toString(Qt.DateFormat.ISODate))
                writer.writeEndElement()
                writer.writeEndElement()

        if widget.displayFormat():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'displayFormat')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(widget.displayFormat())
            writer.writeEndElement()
            writer.writeEndElement()

        if widget.calendarPopup():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'calendarPopup')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()


def write_spin_box_properties(widget, writer):
    """Write QSpinBox/QDoubleSpinBox specific properties"""
    if isinstance(widget, QSpinBox):
        if widget.minimum() != 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'minimum')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.minimum()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.maximum() != 99:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'maximum')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.maximum()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.singleStep() != 1:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'singleStep')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.singleStep()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.value() != 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'value')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.value()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.prefix():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'prefix')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(widget.prefix())
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.suffix():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'suffix')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(widget.suffix())
            writer.writeEndElement()
            writer.writeEndElement()
    elif isinstance(widget, QDoubleSpinBox):
        if widget.minimum() != 0.0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'minimum')
            writer.writeStartElement('double')
            writer.writeCharacters(str(widget.minimum()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.maximum() != 99.99:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'maximum')
            writer.writeStartElement('double')
            writer.writeCharacters(str(widget.maximum()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.singleStep() != 1.0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'singleStep')
            writer.writeStartElement('double')
            writer.writeCharacters(str(widget.singleStep()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.value() != 0.0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'value')
            writer.writeStartElement('double')
            writer.writeCharacters(str(widget.value()))
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.decimals() != 2:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'decimals')
            writer.writeStartElement('number')
            writer.writeCharacters(str(widget.decimals()))
            writer.writeEndElement()
            writer.writeEndElement()


def write_text_edit_properties(widget, writer):
    """Write QTextEdit/QPlainTextEdit specific properties"""
    if isinstance(widget, (QTextEdit, QPlainTextEdit)):
        if widget.isReadOnly():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'readOnly')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.placeholderText():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'placeholderText')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(widget.placeholderText())
            writer.writeEndElement()
            writer.writeEndElement()


def write_check_box_properties(widget, writer):
    """Write QCheckBox/QRadioButton specific properties"""
    if isinstance(widget, (QCheckBox, QRadioButton)):
        if widget.isChecked():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'checked')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()
        if widget.isTristate() and isinstance(widget, QCheckBox):
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'tristate')
            writer.writeStartElement('bool')
            writer.writeCharacters('true')
            writer.writeEndElement()
            writer.writeEndElement()


def write_widget_common_properties(widget, writer, in_layout):
    """Write all common properties for a widget"""
    # styleSheet
    if widget.styleSheet():
        writer.writeStartElement('property')
        writer.writeAttribute('name', 'styleSheet')
        writer.writeStartElement('string')
        writer.writeAttribute('notr', 'true')
        writer.writeCharacters(widget.styleSheet())
        writer.writeEndElement()
        writer.writeEndElement()

    # text property (only for widgets with setText)
    if hasattr(widget, 'setText') and callable(getattr(widget, 'setText')):
        if hasattr(widget, 'text') and callable(getattr(widget, 'text')):
            text_val = widget.text()
            if text_val:
                writer.writeStartElement('property')
                writer.writeAttribute('name', 'text')
                writer.writeStartElement('string')
                writer.writeAttribute('notr', 'true')
                writer.writeCharacters(text_val)
                writer.writeEndElement()
                writer.writeEndElement()

    # placeholderText
    if hasattr(widget, 'placeholderText') and callable(getattr(widget, 'placeholderText')):
        ph = widget.placeholderText()
        if ph:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'placeholderText')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(ph)
            writer.writeEndElement()
            writer.writeEndElement()

    # font
    font = widget.font()
    if font.pointSize() > 0 or font.bold() or font.italic() or font.underline() or font.strikeOut():
        write_font_properties(font, writer)

    # cursor
    write_cursor_property(widget, writer)

    # sizePolicy
    write_size_policy(widget, writer)

    # minimumSize / maximumSize
    write_min_max_size(widget, writer)

    # alignment
    write_alignment(widget, writer)

    # wordWrap
    write_word_wrap(widget, writer)

    # geometry (only for absolute positioned widgets)
    if not in_layout:
        rect = widget.geometry()
        if rect.width() > 0 and rect.height() > 0:
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'geometry')
            writer.writeStartElement('rect')
            writer.writeTextElement('x', str(rect.x()))
            writer.writeTextElement('y', str(rect.y()))
            writer.writeTextElement('width', str(rect.width()))
            writer.writeTextElement('height', str(rect.height()))
            writer.writeEndElement()
            writer.writeEndElement()

    # Frame properties
    write_frame_properties(widget, writer)

    # Type-specific properties
    write_table_properties(widget, writer)
    write_combo_box_properties(widget, writer)
    write_date_edit_properties(widget, writer)
    write_spin_box_properties(widget, writer)
    write_text_edit_properties(widget, writer)
    write_check_box_properties(widget, writer)


def write_widget_in_layout(widget, writer):
    """Write a widget that is managed by a layout"""
    if is_internal_widget(widget):
        return

    class_name = widget.metaObject().className()
    writer.writeStartElement('widget')
    writer.writeAttribute('class', class_name)
    writer.writeAttribute('name', widget.objectName())

    write_widget_common_properties(widget, writer, in_layout=True)

    layout = widget.layout()
    layout_parent = layout.parentWidget() if layout else None
    if layout and not is_internal_widget(layout_parent if layout_parent else widget):
        write_layout(layout, writer)

    if not layout:
        for child in widget.children():
            if child.isWidgetType():
                if not is_internal_widget(child):
                    write_widget_absolute(child, writer)

    writer.writeEndElement()  # widget


def write_widget_absolute(widget, writer):
    """Write a widget with absolute positioning (has geometry, not in parent's layout)"""
    if is_internal_widget(widget):
        return

    class_name = widget.metaObject().className()
    writer.writeStartElement('widget')
    writer.writeAttribute('class', class_name)
    writer.writeAttribute('name', widget.objectName())

    write_widget_common_properties(widget, writer, in_layout=False)

    layout = widget.layout()
    layout_parent = layout.parentWidget() if layout else None
    if layout and not is_internal_widget(layout_parent if layout_parent else widget):
        write_layout(layout, writer)

    if not layout:
        for child in widget.children():
            if child.isWidgetType():
                if not is_internal_widget(child):
                    write_widget_absolute(child, writer)

    writer.writeEndElement()  # widget


# Main generation loop
for UiClass in [
    Ui_HomePage, Ui_OrdersPage, Ui_ClientsPage,
    Ui_ResearchPage, Ui_ReportsPage, Ui_EmployeesPage
]:
    page = QWidget()
    page.setObjectName('page' + UiClass.__name__[6:-4])
    ui = UiClass()
    ui.setupUi(page)

    class_name = UiClass.__name__.replace('Ui_', '').replace('Page', '').lower()
    ui_path = f'ui/pages/{class_name}_page.ui'
    file = QFile(ui_path)
    if file.open(QIODevice.OpenModeFlag.WriteOnly):
        writer = QXmlStreamWriter(file)
        writer.setAutoFormatting(True)
        writer.setAutoFormattingIndent(1)
        writer.writeStartDocument()
        writer.writeStartElement('ui')
        writer.writeAttribute('version', '4.0')
        writer.writeStartElement('class')
        writer.writeCharacters(UiClass.__name__)
        writer.writeEndElement()

        # Write the page widget
        writer.writeStartElement('widget')
        writer.writeAttribute('class', page.metaObject().className())
        writer.writeAttribute('name', page.objectName())

        if page.styleSheet():
            writer.writeStartElement('property')
            writer.writeAttribute('name', 'styleSheet')
            writer.writeStartElement('string')
            writer.writeAttribute('notr', 'true')
            writer.writeCharacters(page.styleSheet())
            writer.writeEndElement()
            writer.writeEndElement()

        layout = page.layout()
        if layout:
            write_layout(layout, writer)

        if not layout:
            for child in page.children():
                if child.isWidgetType() and (layout is None or layout.indexOf(child) == -1):
                    if not is_internal_widget(child):
                        write_widget_absolute(child, writer)

        writer.writeEndElement()  # widget

        writer.writeStartElement('resources')
        writer.writeEndElement()
        writer.writeStartElement('connections')
        writer.writeEndElement()
        writer.writeEndElement()  # ui
        writer.writeEndDocument()
        file.close()
        print(f'Created {ui_path}')
    else:
        print(f'FAILED to open {ui_path}: {file.errorString()}')

print('Done!')
app.quit()