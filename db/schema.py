"""SQL-схема БД. Таблицы создаются только если их ещё нет."""

SCHEMA_SQL = """
-- Сотрудники
CREATE TABLE IF NOT EXISTS employees (
    employee_id INT AUTO_INCREMENT PRIMARY KEY,
    full_name   VARCHAR(200) NOT NULL,
    login       VARCHAR(100) UNIQUE,
    password    VARCHAR(255),
    role        VARCHAR(50) NOT NULL DEFAULT 'ОТК-специалист',
    is_active   TINYINT(1) NOT NULL DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Клиенты (общая таблица)
CREATE TABLE IF NOT EXISTS clients (
    client_id   INT AUTO_INCREMENT PRIMARY KEY,
    client_type ENUM('ЮЛ','ФЛ') NOT NULL,
    phone       VARCHAR(50),
    email       VARCHAR(150),
    is_active   TINYINT(1) NOT NULL DEFAULT 1,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Юридические лица
CREATE TABLE IF NOT EXISTS legal_entities (
    client_id       INT PRIMARY KEY,
    company_name    VARCHAR(300) NOT NULL,
    address         VARCHAR(500),
    inn             VARCHAR(12),
    kpp             VARCHAR(9),
    checking_account VARCHAR(20),
    bik             VARCHAR(9),
    director_name   VARCHAR(200),
    contact_person  VARCHAR(200),
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Физические лица
CREATE TABLE IF NOT EXISTS individuals (
    client_id        INT PRIMARY KEY,
    full_name        VARCHAR(300) NOT NULL,
    birth_date       DATE,
    passport_series  VARCHAR(10),
    passport_number  VARCHAR(10),
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Услуги / исследования
CREATE TABLE IF NOT EXISTS services (
    service_id   INT AUTO_INCREMENT PRIMARY KEY,
    service_name VARCHAR(300) NOT NULL UNIQUE,
    price        DECIMAL(10,2) NOT NULL DEFAULT 0,
    is_active    TINYINT(1) NOT NULL DEFAULT 1
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Заказы
CREATE TABLE IF NOT EXISTS orders (
    order_id    INT AUTO_INCREMENT PRIMARY KEY,
    vessel_code VARCHAR(50) NOT NULL,
    client_id   INT NOT NULL,
    employee_id INT NOT NULL,
    order_date  DATE NOT NULL DEFAULT (CURRENT_DATE),
    status      ENUM('Новый','В работе','Ожидает контроля','На доработке','Завершён','В архиве')
                NOT NULL DEFAULT 'Новый',
    total_price DECIMAL(10,2) NOT NULL DEFAULT 0,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (client_id)   REFERENCES clients(client_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Услуги в заказе (связь многие-ко-многим)
CREATE TABLE IF NOT EXISTS order_services (
    order_service_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id         INT NOT NULL,
    service_id       INT NOT NULL,
    price            DECIMAL(10,2) NOT NULL DEFAULT 0,
    FOREIGN KEY (order_id)   REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Результаты исследований
CREATE TABLE IF NOT EXISTS research_results (
    research_id      INT AUTO_INCREMENT PRIMARY KEY,
    order_service_id INT NOT NULL UNIQUE,
    result_value     TEXT,
    conclusion       TEXT,
    result_date      DATE,
    employee_id      INT,
    created_at       DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (order_service_id) REFERENCES order_services(order_service_id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id)      REFERENCES employees(employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Отчёты
CREATE TABLE IF NOT EXISTS reports (
    report_id   INT AUTO_INCREMENT PRIMARY KEY,
    order_id    INT NOT NULL,
    employee_id INT NOT NULL,
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path   VARCHAR(500),
    FOREIGN KEY (order_id)    REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

# Список всех таблиц, которые должны быть в БД
REQUIRED_TABLES = [
    'employees',
    'clients',
    'legal_entities',
    'individuals',
    'services',
    'orders',
    'order_services',
    'research_results',
    'reports',
]