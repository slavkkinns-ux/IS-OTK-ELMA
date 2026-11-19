from repositories.base_repository import BaseRepository


class ClientRepository(BaseRepository):

    def get_all_clients(self) -> list:
        query = """
        SELECT 
            c.client_id, c.client_type, c.phone, c.email, c.is_active,
            COALESCE(le.company_name, i.full_name,
                    CONCAT('Клиент #', c.client_id)) AS name,
            COALESCE(
                CONCAT('ИНН: ', le.inn),
                CONCAT('Паспорт: ', i.passport_series, ' ', i.passport_number),
                '—'
            ) AS details,
            COALESCE(le.contact_person, i.full_name, '—') AS contact_person
        FROM clients c
        LEFT JOIN legal_entities le ON le.client_id = c.client_id
        LEFT JOIN individuals    i  ON i.client_id  = c.client_id
        WHERE c.is_active = 1
        ORDER BY name
        """
        return self.execute_query(query)

    def get_client_by_id(self, client_id: int) -> dict:
        """Получить клиента по ID."""
        query = """
        SELECT 
            c.*,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.company_name
                WHEN c.client_type = 'ФЛ' THEN i.full_name
            END AS name,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.inn
                WHEN c.client_type = 'ФЛ' THEN CONCAT(i.passport_series, i.passport_number)
            END AS identifier
        FROM clients c
        LEFT JOIN legal_entities le ON c.client_id = le.client_id AND c.client_type = 'ЮЛ'
        LEFT JOIN individuals i ON c.client_id = i.client_id AND c.client_type = 'ФЛ'
        WHERE c.client_id = %s
        """
        results = self.execute_query(query, (client_id,))
        return results[0] if results else None

    def get_clients_stats(self) -> dict:
        """Статистика по клиентам."""
        query = """
        SELECT 
            COUNT(*) AS total_clients,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) AS active_clients,
            COUNT(DISTINCT o.client_id) AS clients_with_orders
        FROM clients c
        LEFT JOIN orders o ON c.client_id = o.client_id
        """
        results = self.execute_query(query)
        return results[0] if results else {}