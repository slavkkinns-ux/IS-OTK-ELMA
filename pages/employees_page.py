"""Страница управления сотрудниками."""
from PyQt6.QtWidgets import (QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QHeaderView, QComboBox, QLineEdit, QCheckBox,
                             QGroupBox, QMessageBox, QAbstractItemView)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from db.report_repo import (
    get_all_employees, get_employee_stats, reset_password, 
    update_employee, get_employee
)
from dialogs.employee_dialog import EmployeeDialog, ROLE_DISPLAY


class EmployeesPage(QWidget):
    """Страница управления сотрудниками."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._init_ui()
        self._load_data()
    
    def _init_ui(self):
        """Инициализация интерфейса."""
        from PyQt6 import QtCore, QtGui
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Заголовок
        lbl_title = QLabel("Управление сотрудниками")
        lbl_title.setStyleSheet("font-size: 18pt; font-weight: bold; color: #174A7E;")
        main_layout.addWidget(lbl_title)
        
        lbl_subtitle = QLabel("Добавление и управление учётными записями персонала")
        lbl_subtitle.setStyleSheet("font-size: 10pt; color: #7F8C8D;")
        main_layout.addWidget(lbl_subtitle)
        
        # Карточки статистики
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(10)
        
        self.stat_cards = {}
        stats_config = [
            ('total', 'Всего'),
            ('active', 'Активных'),
            ('managers', 'Менеджеров'),
            ('lab_technicians', 'Лаборантов'),
            ('controllers', 'Контролёров'),
            ('admins', 'Админов'),
        ]

        for key, title in stats_config:
            card = self._create_stat_card(title)
            stats_layout.addWidget(card, stretch=1)
            self.stat_cards[key] = card
        
        main_layout.addLayout(stats_layout)
        
        # Панель фильтров
        filter_group = QGroupBox("Фильтры")
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск по ФИО или логину...")
        filter_layout.addWidget(self.search_edit, stretch=2)
        
        self.combo_role_filter = QComboBox()
        self.combo_role_filter.addItem("Все роли", None)
        for role_key, role_name in ROLE_DISPLAY.items():
            self.combo_role_filter.addItem(role_name, role_key)
        filter_layout.addWidget(self.combo_role_filter)
        
        self.check_active_only = QCheckBox("Только активные")
        self.check_active_only.setChecked(True)
        filter_layout.addWidget(self.check_active_only)
        
        btn_search = QPushButton("Поиск")
        btn_search.setStyleSheet("""
            QPushButton {
                background-color: #2D83D5;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3B94E8; }
        """)
        btn_search.clicked.connect(self._load_data)
        filter_layout.addWidget(btn_search)
        
        btn_reset = QPushButton("Сбросить")
        btn_reset.clicked.connect(self._reset_filters)
        filter_layout.addWidget(btn_reset)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Таблица сотрудников
        self.table_employees = QTableWidget()
        self.table_employees.setColumnCount(9)
        self.table_employees.setHorizontalHeaderLabels([
            "№", "ФИО", "Логин", "Роль", "Статус", 
            "Исследований", "Отчётов", "Дата добавления", "Действия"
        ])
        
        self.table_employees.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table_employees.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.table_employees.setAlternatingRowColors(True)
        self.table_employees.verticalHeader().setVisible(False)
        
        # Настройка заголовков
        header = self.table_employees.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(7, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(8, QHeaderView.ResizeMode.Fixed)
        
        # Фиксированная ширина для узких колонок
        self.table_employees.setColumnWidth(0, 50)
        self.table_employees.setColumnWidth(5, 90)
        self.table_employees.setColumnWidth(6, 70)
        self.table_employees.setColumnWidth(7, 110)
        self.table_employees.setColumnWidth(8, 220)
        self.table_employees.verticalHeader().setDefaultSectionSize(50)
        self.table_employees.verticalHeader().setMinimumSectionSize(50)

        # Минимальная ширина для всех колонок
        header.setMinimumSectionSize(80)
        
        self.table_employees.setStyleSheet("""
            QTableWidget {
                background-color: #FFFFFF;
                border: 1px solid #D8E3EF;
                border-radius: 8px;
                gridline-color: #D8E3EF;
                font-size: 10pt;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QHeaderView::section {
                background-color: #174A7E;
                color: white;
                padding: 10px;
                border: none;
                font-weight: bold;
                font-size: 10pt;
            }
        """)
        
        main_layout.addWidget(self.table_employees, stretch=1)
        
        # Кнопки действий
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_add = QPushButton("+ Добавить сотрудника")
        self.btn_add.setStyleSheet("""
            QPushButton {
                background-color: #27AE60;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
                font-size: 10pt;
            }
            QPushButton:hover { background-color: #2ECC71; }
        """)
        self.btn_add.clicked.connect(self._on_add_employee)
        btn_layout.addWidget(self.btn_add)
        
        self.btn_refresh = QPushButton("↻ Обновить")
        self.btn_refresh.clicked.connect(self._load_data)
        btn_layout.addWidget(self.btn_refresh)
        
        main_layout.addLayout(btn_layout)
    
    def _create_stat_card(self, title: str) -> QGroupBox:
        """Создать карточку статистики в едином стиле."""
        card = QGroupBox()
        card.setStyleSheet("""
            QGroupBox {
                background-color: #F0F5FA;
                border: 2px solid #174A7E;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)
        
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("""
            font-size: 10pt; 
            color: #174A7E; 
            font-weight: bold;
        """)
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_title.setWordWrap(True)
        layout.addWidget(lbl_title)
        
        lbl_value = QLabel("0")
        lbl_value.setStyleSheet("""
            font-size: 24pt; 
            font-weight: bold; 
            color: #2D83D5;
        """)
        lbl_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_value)
        
        card.lbl_value = lbl_value
        
        return card
    
    def _load_data(self):
        """Загрузить данные сотрудников."""
        search_query = self.search_edit.text().strip() or None
        role_filter = self.combo_role_filter.currentData()
        active_only = self.check_active_only.isChecked()
        
        employees = get_all_employees(
            role_filter=role_filter,
            active_only=active_only,
            search_query=search_query
        )
        
        self.table_employees.setRowCount(len(employees))
        
        for row_idx, emp in enumerate(employees):
            # №
            item_id = QTableWidgetItem(str(row_idx + 1))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_employees.setItem(row_idx, 0, item_id)
            
            # ФИО
            self.table_employees.setItem(row_idx, 1, QTableWidgetItem(emp.get('full_name', '')))
            
            # Логин
            self.table_employees.setItem(row_idx, 2, QTableWidgetItem(emp.get('login', '')))
            
            # Роль (с цветом)
            role = emp.get('role', '')
            role_name = ROLE_DISPLAY.get(role, role)
            item_role = QTableWidgetItem(role_name)
            item_role.setForeground(QColor("white"))
            
            # Цвета ролей
            role_colors = {
                'admin': '#C0392B',
                'controller': '#2980B9',
                'lab_technician': '#27AE60',
                'manager': '#F39C12',
            }
            item_role.setBackground(QColor(role_colors.get(role, '#95A5A6')))
            item_role.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_employees.setItem(row_idx, 3, item_role)
            
            # Статус
            is_active = emp.get('is_active', 1)
            status_text = "Активен" if is_active else "Деактивирован"
            item_status = QTableWidgetItem(status_text)
            item_status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_employees.setItem(row_idx, 4, item_status)
            
            # Исследований
            research_count = emp.get('research_count', 0)
            item_research = QTableWidgetItem(str(research_count))
            item_research.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_employees.setItem(row_idx, 5, item_research)
            
            # Отчётов
            report_count = emp.get('report_count', 0)
            item_report = QTableWidgetItem(str(report_count))
            item_report.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_employees.setItem(row_idx, 6, item_report)
            
            # Дата добавления
            created_at = emp.get('created_at')
            if created_at:
                if hasattr(created_at, 'strftime'):
                    date_str = created_at.strftime('%d.%m.%Y')
                else:
                    date_str = str(created_at)
            else:
                date_str = '-'
            self.table_employees.setItem(row_idx, 7, QTableWidgetItem(date_str))
            
            # Действия
            from session import Session
            current_user_id = Session.get_user_id()
            is_other_admin = (emp.get('role') == 'admin' and emp['employee_id'] != current_user_id)

            actions_widget = QWidget()
            actions_layout = QHBoxLayout(actions_widget)
            actions_layout.setContentsMargins(2, 2, 2, 2)
            actions_layout.setSpacing(4)

            btn_edit = QPushButton("Изм")
            btn_edit.setToolTip("Редактировать" if not is_other_admin else "Только для своего аккаунта")
            btn_edit.setFixedSize(65, 32)
            btn_edit.setEnabled(not is_other_admin)  # ← отключаем для чужих админов
            btn_edit.setStyleSheet("""
                QPushButton {
                    background-color: #3498DB;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #2980B9; }
                QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; }
            """)
            btn_edit.clicked.connect(lambda checked, eid=emp['employee_id']: self._on_edit_employee(eid))
            actions_layout.addWidget(btn_edit)

            btn_reset = QPushButton("Пар")
            btn_reset.setToolTip("Сбросить пароль" if not is_other_admin else "Только для своего аккаунта")
            btn_reset.setFixedSize(65, 32)
            btn_reset.setEnabled(not is_other_admin)
            btn_reset.setStyleSheet("""
                QPushButton {
                    background-color: #F39C12;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #E67E22; }
                QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; }
            """)
            btn_reset.clicked.connect(lambda checked, eid=emp['employee_id']: self._on_reset_password(eid))
            actions_layout.addWidget(btn_reset)

            btn_toggle = QPushButton("Блок" if is_active else "Разб")
            btn_toggle.setToolTip("Деактивировать" if is_active else "Активировать" if not is_other_admin else "Только для своего аккаунта")
            btn_toggle.setFixedSize(65, 32)
            btn_toggle.setEnabled(not is_other_admin)
            btn_toggle.setStyleSheet("""
                QPushButton {
                    background-color: #E74C3C;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    font-size: 10pt;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #C0392B; }
                QPushButton:disabled { background-color: #BDC3C7; color: #7F8C8D; }
            """)
            btn_toggle.clicked.connect(lambda checked, eid=emp['employee_id']: self._on_toggle_employee_status(eid))
            actions_layout.addWidget(btn_toggle)

            self.table_employees.setCellWidget(row_idx, 8, actions_widget)
        
        self._update_stats()
    
    def _update_stats(self):
        """Обновить карточки статистики."""
        stats = get_employee_stats()
        if stats:
            self.stat_cards['total'].lbl_value.setText(str(stats.get('total', 0)))
            self.stat_cards['active'].lbl_value.setText(str(stats.get('active', 0)))
            self.stat_cards['managers'].lbl_value.setText(str(stats.get('managers', 0)))
            self.stat_cards['lab_technicians'].lbl_value.setText(str(stats.get('lab_technicians', 0)))
            self.stat_cards['controllers'].lbl_value.setText(str(stats.get('controllers', 0)))
            self.stat_cards['admins'].lbl_value.setText(str(stats.get('admins', 0)))
    
    def _reset_filters(self):
        """Сбросить фильтры."""
        self.search_edit.clear()
        self.combo_role_filter.setCurrentIndex(0)
        self.check_active_only.setChecked(True)
        self._load_data()
    
    def _on_add_employee(self):
        """Открыть диалог добавления сотрудника."""
        dialog = EmployeeDialog(self)
        if dialog.exec() == EmployeeDialog.DialogCode.Accepted:
            self._load_data()
            QMessageBox.information(self, "Готово", "Сотрудник успешно добавлен.")
    
    def _on_edit_employee(self, employee_id: int):
        """Открыть диалог редактирования сотрудника."""
        dialog = EmployeeDialog(self, employee_id=employee_id)
        if dialog.exec() == EmployeeDialog.DialogCode.Accepted:
            self._load_data()
            QMessageBox.information(self, "Готово", "Данные сотрудника обновлены.")
    
    def _on_reset_password(self, employee_id: int):
        """Сбросить пароль сотрудника."""
        reply = QMessageBox.question(
            self, "Сброс пароля",
            "Сбросить пароль сотрудника на '123456'?\n\n"
            "Сотрудник будет обязан сменить пароль при следующем входе.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                reset_password(employee_id)
                QMessageBox.information(self, "Готово", "Пароль сброшен на '123456'.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сбросить пароль:\n{e}")
    
    def _on_toggle_employee_status(self, employee_id: int):
        """Переключить статус сотрудника."""
        from session import Session
        
        emp = get_employee(employee_id)
        if not emp:
            return
        
        current_user_id = Session.get_user_id()
        is_active = emp.get('is_active', 1)
        new_status = not is_active
        
        # ЗАЩИТА 1: Админы не могут деактивировать других админов (только себя)
        if emp.get('role') == 'admin' and emp['employee_id'] != current_user_id:
            QMessageBox.critical(
                self, "Отказ в доступе",
                "Вы не можете деактивировать другого администратора.\n\n"
                "Изменить статус можно только для своей учётной записи."
            )
            return
        
        # ЗАЩИТА 2: Нельзя деактивировать последнего активного админа
        if emp.get('role') == 'admin' and not new_status:
            all_active_admins = get_all_employees(role_filter='admin', active_only=True)
            if len(all_active_admins) <= 1:
                QMessageBox.critical(
                    self, "Отказ в доступе",
                    "Нельзя деактивировать последнего активного администратора!\n\n"
                    "Система должна иметь хотя бы одного активного администратора."
                )
                return
        
        action = "активировать" if new_status else "деактивировать"
        
        reply = QMessageBox.question(
            self, "Изменение статуса",
            f"Вы уверены, что хотите {action} сотрудника?\n\n"
            f"ФИО: {emp.get('full_name', '')}\n"
            f"Логин: {emp.get('login', '')}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            try:
                update_employee(employee_id, is_active=new_status)
                self._load_data()
                status_text = "активирован" if new_status else "деактивирован"
                QMessageBox.information(self, "Готово", f"Сотрудник {status_text}.")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось изменить статус:\n{e}")