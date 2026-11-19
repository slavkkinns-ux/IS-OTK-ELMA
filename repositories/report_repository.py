from repositories.base_repository import BaseRepository


class ReportRepository(BaseRepository):

    def get_research_queue(self) -> list:
        """Очередь исследований."""
        query = """
        SELECT 
            o.order_id,
            o.vessel_code,
            s.service_name,
            CASE 
                WHEN c.client_type = 'ЮЛ' THEN le.company_name
                WHEN c.client_type = 'ФЛ' THEN i.full_name
            END AS client_name,
            rr.result_value
        FROM order_services os
        JOIN orders o ON os.order_id = o.order_id
        JOIN services s ON os.service_id = s.service_id
        JOIN clients c ON o.client_id = c.client_id
        LEFT JOIN legal_entities le ON c.client_id = le.client_id AND c.client_type = 'ЮЛ'
        LEFT JOIN individuals i ON c.client_id = i.client_id AND c.client_type = 'ФЛ'
        LEFT JOIN research_results rr ON os.order_service_id = rr.order_service_id
        WHERE o.status IN ('В работе', 'Ожидает проверки')
        ORDER BY o.order_date DESC
        """
        return self.execute_query(query)

    def get_report_research(self, order_id: int) -> list:
        """Исследования для отчёта."""
        query = """
        SELECT 
            s.service_name,
            os.price_at_order,
            rr.result_value,
            rr.conclusion
        FROM order_services os
        JOIN services s ON os.service_id = s.service_id
        LEFT JOIN research_results rr ON os.order_service_id = rr.order_service_id
        WHERE os.order_id = %s
        """
        return self.execute_query(query, (order_id,))

    def get_recent_reports(self, limit: int = 5) -> list:
        query = """
        SELECT 
            r.report_id,
            o.vessel_code,
            r.report_date,
            e.full_name AS employee_name
        FROM reports r
        JOIN orders o ON r.order_id = o.order_id
        JOIN employees e ON r.employee_id = e.employee_id
        ORDER BY r.report_date DESC
        LIMIT %s
        """
        return self.execute_query(query, (limit,))