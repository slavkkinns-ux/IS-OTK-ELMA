# Пример конфигурации для config.py (fallback, если config.json не найден)
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'your_password',
    'database': 'elma',
    'charset': 'utf8mb4'
}

# Рекомендуемый формат: config.json (создаётся автоматически при первом запуске)
# {
#     "host": "localhost",
#     "port": 3306,
#     "user": "root",
#     "password": "",
#     "database": "elma",
#     "charset": "utf8mb4"
# }