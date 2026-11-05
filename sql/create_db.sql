-- 1. Указываем, что работаем с базой elma
USE elma;

-- 2. Удаляем старые таблицы, если они существовали (чтобы не было ошибок)
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS order_services;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS services;
DROP TABLE IF EXISTS legal_entities;
DROP TABLE IF EXISTS individuals;
DROP TABLE IF EXISTS clients;
DROP TABLE IF EXISTS action_logs;
DROP TABLE IF EXISTS employees;

-- 3. СОЗДАЕМ ТАБЛИЦЫ

-- Сотрудники
CREATE TABLE employees (
    employee_id INT PRIMARY KEY AUTO_INCREMENT,
    full_name VARCHAR(255) NOT NULL,
    login VARCHAR(100) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,
    is_active TINYINT DEFAULT 1
);

-- Журнал действий
CREATE TABLE action_logs (
    log_id INT PRIMARY KEY AUTO_INCREMENT,
    employee_id INT NOT NULL,
    action VARCHAR(100) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Общая таблица клиентов
CREATE TABLE clients (
    client_id INT PRIMARY KEY AUTO_INCREMENT,
    client_type VARCHAR(2) NOT NULL, -- 'FL' или 'UL'
    phone VARCHAR(20) NOT NULL,
    email VARCHAR(254)
);

-- Физ. лица (ФЛ)
CREATE TABLE individuals (
    client_id INT PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    birth_date DATE NOT NULL,
    passport_series VARCHAR(4) NOT NULL,
    passport_number VARCHAR(6) NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Юр. лица (ЮЛ)
CREATE TABLE legal_entities (
    client_id INT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    address VARCHAR(255) NOT NULL,
    inn VARCHAR(12) NOT NULL UNIQUE,
    kpp VARCHAR(9),
    checking_account VARCHAR(20) NOT NULL,
    bik VARCHAR(9) NOT NULL,
    director_name VARCHAR(255) NOT NULL,
    contact_person VARCHAR(255) NOT NULL,
    FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Справочник услуг
CREATE TABLE services (
    service_id INT PRIMARY KEY AUTO_INCREMENT,
    service_name VARCHAR(255) NOT NULL,
    price DECIMAL(10,2) NOT NULL,
    is_active TINYINT DEFAULT 1
);

-- Заказы
CREATE TABLE orders (
    order_id INT PRIMARY KEY AUTO_INCREMENT,
    vessel_code VARCHAR(50) NOT NULL UNIQUE,
    client_id INT NOT NULL,
    employee_id INT NOT NULL,
    order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) NOT NULL DEFAULT 'Новый',
    FOREIGN KEY (client_id) REFERENCES clients(client_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);

-- Услуги в заказе
CREATE TABLE order_services (
    order_service_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    service_id INT NOT NULL,
    price_at_order DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(service_id)
);

-- Отчеты
CREATE TABLE reports (
    report_id INT PRIMARY KEY AUTO_INCREMENT,
    order_id INT NOT NULL,
    employee_id INT NOT NULL,
    report_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(500),
    FOREIGN KEY (order_id) REFERENCES orders(order_id),
    FOREIGN KEY (employee_id) REFERENCES employees(employee_id)
);