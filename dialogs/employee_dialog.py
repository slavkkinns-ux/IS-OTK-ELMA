"""Диалог добавления/редактирования сотрудника."""
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                             QLineEdit, QComboBox, QCheckBox, QPushButton,
                             QMessageBox, QFormLayout, QGroupBox)
from PyQt6.QtCore import Qt
from db.report_repo import check_login_exists, get_employee

# Маппинг ролей для отображения
ROLE_DISPLAY = {
    'manager': 'Менеджер',
    'lab_technician': 'Лаборант',
    'controller': 'Контролёр',
    'admin': 'Администратор',
}

ROLE_DESCRIPTIONS = {
    'manager': '✓ Создание заказов\n✓ Просмотр заказов\n✗ Исследования\n✗ Отчёты',
    'lab_technician': '✓ Создание заказов\n✓ Просмотр заказов\n✓ Исследования\n✓ Отчёты',
    'controller': '✓ Создание заказов\n✓ Просмотр заказов\n✓ Исследования\n✓ Отчёты',
    'admin': '✓ Все функции\n✓ Управление сотрудниками\n✓ Просмотр логов',
}


class EmployeeDialog(QDialog):
    """Диалог для добавления или редактирования сотрудника."""
    
    def __init__(self, parent=None, employee_id=None):
        super().__init__(parent)
        self.employee_id = employee_id
        self.setWindowTitle("Редактирование сотрудника" if employee_id else "Добавление сотрудника")
        self.setMinimumWidth(500)
        
        self._init_ui()
        
        if employee_id:
            self._load_employee_data()
    
    def _init_ui(self):
        layout = QVBoxLayout(self)
        
        # Основная форма
        form_group = QGroupBox("Данные сотрудника")
        form_layout = QFormLayout()
        
        # ФИО
        self.edit_full_name = QLineEdit()
        self.edit_full_name.setPlaceholderText("Иванов Иван Иванович")
        form_layout.addRow("ФИО *:", self.edit_full_name)
        
        # Логин
        self.edit_login = QLineEdit()
        self.edit_login.setPlaceholderText("ivanov")
        form_layout.addRow("Логин *:", self.edit_login)
        
        # Пароль (только при создании)
        if not self.employee_id:
            self.edit_password = QLineEdit()
            self.edit_password.setEchoMode(QLineEdit.EchoMode.Password)
            self.edit_password.setPlaceholderText("Минимум 6 символов")
            form_layout.addRow("Пароль *:", self.edit_password)
        
        # Роль
        self.combo_role = QComboBox()
        for role_key, role_name in ROLE_DISPLAY.items():
            self.combo_role.addItem(role_name, role_key)
        self.combo_role.currentIndexChanged.connect(self._on_role_changed)
        form_layout.addRow("Роль *:", self.combo_role)
        
        # Статус
        self.check_active = QCheckBox("Активен")
        self.check_active.setChecked(True)
        form_layout.addRow("Статус:", self.check_active)
        
        # Email
        self.edit_email = QLineEdit()
        self.edit_email.setPlaceholderText("email@example.com")
        form_layout.addRow("Email:", self.edit_email)
        
        # Телефон
        self.edit_phone = QLineEdit()
        self.edit_phone.setPlaceholderText("+7 (999) 123-45-67")
        form_layout.addRow("Телефон:", self.edit_phone)
        
        form_group.setLayout(form_layout)
        layout.addWidget(form_group)
        
        # Описание роли
        self.lbl_role_description = QLabel()
        self.lbl_role_description.setStyleSheet("""
            QLabel {
                background-color: #F0F5FA;
                border: 1px solid #D8E3EF;
                border-radius: 6px;
                padding: 10px;
                font-size: 9pt;
            }
        """)
        layout.addWidget(self.lbl_role_description)
        
        # Кнопки
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        btn_save = QPushButton("Сохранить")
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2D83D5;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3B94E8;
            }
        """)
        btn_save.clicked.connect(self._save)
        btn_layout.addWidget(btn_save)
        
        btn_cancel = QPushButton("Отмена")
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(btn_cancel)
        
        layout.addLayout(btn_layout)
        
        # Инициализация описания роли
        self._on_role_changed(0)
    
    def _on_role_changed(self, index):
        """Обновить описание при смене роли."""
        role_key = self.combo_role.itemData(index)
        if role_key:
            self.lbl_role_description.setText(f"<b>{ROLE_DISPLAY[role_key]}:</b>\n{ROLE_DESCRIPTIONS[role_key]}")
    
    def _load_employee_data(self):
        """Загрузить данные сотрудника для редактирования."""
        from db.report_repo import get_employee
        emp = get_employee(self.employee_id)
        if not emp:
            return
        
        self.edit_full_name.setText(emp.get('full_name', ''))
        self.edit_login.setText(emp.get('login', ''))
        self.edit_login.setReadOnly(True)  # Логин нельзя менять
        self.check_active.setChecked(bool(emp.get('is_active', 1)))
        self.edit_email.setText(emp.get('email', '') or '')
        self.edit_phone.setText(emp.get('phone', '') or '')
        
        # Установить роль
        role = emp.get('role', 'lab_technician')
        for i in range(self.combo_role.count()):
            if self.combo_role.itemData(i) == role:
                self.combo_role.setCurrentIndex(i)
                break
    
    def _save(self):
        """Сохранить сотрудника."""
        from session import Session
        
        full_name = self.edit_full_name.text().strip()
        login = self.edit_login.text().strip()
        role = self.combo_role.currentData()
        is_active = self.check_active.isChecked()
        email = self.edit_email.text().strip() or None
        phone = self.edit_phone.text().strip() or None
        
        # Валидация
        if not full_name:
            QMessageBox.warning(self, "Ошибка", "Введите ФИО.")
            return
        
        if not login:
            QMessageBox.warning(self, "Ошибка", "Введите логин.")
            return
        
        if len(login) < 3:
            QMessageBox.warning(self, "Ошибка", "Логин должен содержать минимум 3 символа.")
            return
        
        # Проверка уникальности логина
        from db.report_repo import check_login_exists
        if check_login_exists(login, exclude_employee_id=self.employee_id):
            QMessageBox.warning(self, "Ошибка", "Этот логин уже занят.")
            return
        
        # ===== ЗАЩИТЫ =====
        current_user_id = Session.get_employee_id()
        
        # При РЕДАКТИРОВАНИИ: админ не может менять роль/статус другого админа
        if self.employee_id and self.employee_id != current_user_id:
            from db.report_repo import get_employee
            emp = get_employee(self.employee_id)
            if emp and emp.get('role') == 'admin':
                QMessageBox.critical(
                    self, "Отказ в доступе",
                    "Вы не можете изменять данные другого администратора.\n\n"
                    "Редактировать можно только свою учётную запись."
                )
                return
        
        # При РЕДАКТИРОВАНИИ: нельзя понизить последнего активного админа
        if self.employee_id and self.employee_id == current_user_id:
            if role != 'admin':
                from db.report_repo import get_all_employees
                all_active_admins = get_all_employees(role_filter='admin', active_only=True)
                # Если текущий пользователь — единственный активный админ, нельзя понизить себя
                if len(all_active_admins) <= 1:
                    QMessageBox.critical(
                        self, "Отказ в доступе",
                        "Вы — последний активный администратор системы.\n\n"
                        "Нельзя изменить свою роль, пока не будет создан другой администратор."
                    )
                    return
        
        try:
            from db.report_repo import create_employee, update_employee
            
            if self.employee_id:
                # Редактирование
                update_employee(
                    self.employee_id,
                    full_name=full_name,
                    role=role,
                    is_active=is_active,
                    email=email,
                    phone=phone
                )
            else:
                # Создание
                password = self.edit_password.text()
                if len(password) < 6:
                    QMessageBox.warning(self, "Ошибка", "Пароль должен содержать минимум 6 символов.")
                    return
                
                create_employee(
                    full_name=full_name,
                    login=login,
                    password=password,
                    role=role,
                    is_active=is_active,
                    email=email,
                    phone=phone
                )
            
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить:\n{e}")