CREATE TABLE `action_logs` (
  `log_id` int NOT NULL AUTO_INCREMENT,
  `employee_id` int NOT NULL,
  `action` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`log_id`),
  KEY `employee_id` (`employee_id`),
  CONSTRAINT `action_logs_ibfk_1` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `clients` (
  `client_id` int NOT NULL AUTO_INCREMENT,
  `client_type` enum('ЮЛ','ФЛ') NOT NULL,
  `password_hash` varchar(64) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT '1',
  `phone` varchar(20) NOT NULL,
  `email` varchar(254) DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`client_id`),
  CONSTRAINT `chk_client_type` CHECK ((`client_type` in (_utf8mb4'ФЛ',_utf8mb4'ЮЛ')))
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `employees` (
  `employee_id` int NOT NULL AUTO_INCREMENT,
  `full_name` varchar(255) NOT NULL,
  `login` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `role` enum('manager','lab_technician','controller','admin') NOT NULL,
  `is_active` tinyint DEFAULT '1',
  `must_change_password` tinyint(1) NOT NULL DEFAULT '0',
  `email` varchar(100) DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `last_login` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` int DEFAULT NULL,
  PRIMARY KEY (`employee_id`),
  UNIQUE KEY `login` (`login`),
  UNIQUE KEY `uk_employees_login` (`login`),
  KEY `idx_employees_role` (`role`),
  KEY `idx_employees_is_active` (`is_active`),
  KEY `fk_employees_created_by` (`created_by`),
  CONSTRAINT `fk_employees_created_by` FOREIGN KEY (`created_by`) REFERENCES `employees` (`employee_id`) ON DELETE SET NULL
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `individuals` (
  `client_id` int NOT NULL,
  `full_name` varchar(255) NOT NULL,
  `birth_date` date NOT NULL,
  `passport_series` varchar(4) NOT NULL,
  `passport_number` varchar(6) NOT NULL,
  PRIMARY KEY (`client_id`),
  CONSTRAINT `individuals_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `legal_entities` (
  `client_id` int NOT NULL,
  `company_name` varchar(255) NOT NULL,
  `address` varchar(255) NOT NULL,
  `inn` varchar(12) NOT NULL,
  `kpp` varchar(9) DEFAULT NULL,
  `checking_account` varchar(20) NOT NULL,
  `bik` varchar(9) NOT NULL,
  `director_name` varchar(255) NOT NULL,
  `contact_person` varchar(255) NOT NULL,
  PRIMARY KEY (`client_id`),
  UNIQUE KEY `inn` (`inn`),
  CONSTRAINT `legal_entities_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`) ON DELETE CASCADE
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `order_services` (
  `order_service_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `service_id` int NOT NULL,
  `price_at_order` decimal(10,2) NOT NULL,
  `price` decimal(10,2) NOT NULL DEFAULT '0.00',
  PRIMARY KEY (`order_service_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_service_id` (`service_id`),
  CONSTRAINT `order_services_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`) ON DELETE CASCADE,
  CONSTRAINT `order_services_ibfk_2` FOREIGN KEY (`service_id`) REFERENCES `services` (`service_id`)
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `orders` (
  `order_id` int NOT NULL AUTO_INCREMENT,
  `vessel_code` varchar(50) NOT NULL,
  `client_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `order_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) NOT NULL DEFAULT 'Новый',
  `total_price` decimal(10,2) NOT NULL DEFAULT '0.00',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`order_id`),
  KEY `idx_orders_vessel_code` (`vessel_code`),
  KEY `idx_client_id` (`client_id`),
  KEY `idx_employee_id` (`employee_id`),
  KEY `idx_status` (`status`),
  CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`client_id`) REFERENCES `clients` (`client_id`),
  CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `reports` (
  `report_id` int NOT NULL AUTO_INCREMENT,
  `order_id` int NOT NULL,
  `employee_id` int NOT NULL,
  `report_date` datetime DEFAULT CURRENT_TIMESTAMP,
  `file_path` varchar(500) DEFAULT NULL,
  PRIMARY KEY (`report_id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_employee_id` (`employee_id`),
  CONSTRAINT `reports_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`order_id`),
  CONSTRAINT `reports_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `research_results` (
  `research_id` int NOT NULL AUTO_INCREMENT,
  `order_service_id` int NOT NULL,
  `result_value` varchar(255) DEFAULT NULL,
  `conclusion` text,
  `result_date` date DEFAULT NULL,
  `employee_id` int DEFAULT NULL,
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`research_id`),
  KEY `idx_order_service_id` (`order_service_id`),
  KEY `idx_employee_id` (`employee_id`),
  CONSTRAINT `research_results_ibfk_1` FOREIGN KEY (`order_service_id`) REFERENCES `order_services` (`order_service_id`) ON DELETE CASCADE,
  CONSTRAINT `research_results_ibfk_2` FOREIGN KEY (`employee_id`) REFERENCES `employees` (`employee_id`)
) ENGINE=InnoDB CHARSET=utf8mb4;

CREATE TABLE `services` (
  `service_id` int NOT NULL AUTO_INCREMENT,
  `service_name` varchar(255) NOT NULL,
  `price` decimal(10,2) NOT NULL,
  `is_active` tinyint DEFAULT '1',
  PRIMARY KEY (`service_id`)
) ENGINE=InnoDB CHARSET=utf8mb4
