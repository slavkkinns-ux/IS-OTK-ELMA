"""Unit-тесты для ReportService."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from services.report_service import ReportService


class TestReportServiceResearch:
    """Тесты очереди исследований и результатов."""

    def test_get_research_queue(self, report_service, report_repo_mock):
        """Получение очереди исследований."""
        report_repo_mock.get_research_queue.return_value = [
            {"order_service_id": 1, "order_id": 1, "service_name": "Услуга 1"}
        ]

        result = report_service.get_research_queue()

        assert len(result) == 1
        report_repo_mock.get_research_queue.assert_called_once()

    def test_get_research_result_success(self, report_service, report_repo_mock):
        """Получение результата исследования."""
        report_repo_mock.get_research_result.return_value = {
            "order_service_id": 1, "result_value": "OK"
        }

        result = report_service.get_research_result(1)

        assert result["order_service_id"] == 1

    def test_get_research_result_invalid_id_raises(self, report_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID услуги заказа"):
            report_service.get_research_result(0)

    def test_save_research_result_success(self, report_service, report_repo_mock):
        """Сохранение результата исследования."""
        report_repo_mock.save_research_result.return_value = 42

        result = report_service.save_research_result(
            order_service_id=1,
            employee_id=1,
            result_value="Результат",
            conclusion="Вывод",
            result_date=date.today(),
        )

        assert result == 42
        report_repo_mock.save_research_result.assert_called_once()

    def test_save_research_result_invalid_order_service_id_raises(self, report_service):
        """Некорректный order_service_id — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID услуги заказа"):
            report_service.save_research_result(0, 1, "val", "concl", date.today())

    def test_save_research_result_invalid_employee_id_raises(self, report_service):
        """Некорректный employee_id — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID сотрудника"):
            report_service.save_research_result(1, 0, "val", "concl", date.today())

    def test_get_report_research(self, report_service, report_repo_mock):
        """Исследования по заказу для отчёта."""
        report_repo_mock.get_report_research.return_value = [
            {"order_service_id": 1, "result_value": "OK"}
        ]

        result = report_service.get_report_research(1)

        assert len(result) == 1
        report_repo_mock.get_report_research.assert_called_once_with(1)

    def test_get_report_research_invalid_id_raises(self, report_service):
        """Некорректный ID заказа — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID заказа"):
            report_service.get_report_research(0)


class TestReportServiceReports:
    """Тесты отчётов."""

    def test_get_recent_reports(self, report_service, report_repo_mock):
        """Последние отчёты."""
        report_repo_mock.get_recent_reports.return_value = [
            {"report_id": 1, "order_id": 1}
        ]

        result = report_service.get_recent_reports(5)

        assert len(result) == 1
        report_repo_mock.get_recent_reports.assert_called_once_with(5)

    def test_get_recent_reports_invalid_limit_raises(self, report_service):
        """Некорректный лимит — ValueError."""
        with pytest.raises(ValueError, match="Некорректный лимит"):
            report_service.get_recent_reports(0)

    def test_get_report_success(self, report_service, report_repo_mock):
        """Получение отчёта по ID."""
        report_repo_mock.get_report.return_value = {"report_id": 1, "file_path": "/path"}

        result = report_service.get_report(1)

        assert result["report_id"] == 1

    def test_get_report_invalid_id_raises(self, report_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID отчёта"):
            report_service.get_report(0)

    def test_get_report_by_order(self, report_service, report_repo_mock):
        """Отчёт по заказу."""
        report_repo_mock.get_report_by_order.return_value = {"report_id": 1}

        result = report_service.get_report_by_order(1)

        assert result["report_id"] == 1

    def test_create_report_success(self, report_service, report_repo_mock):
        """Создание отчёта."""
        report_repo_mock.create_report.return_value = 42

        result = report_service.create_report(order_id=1, employee_id=1, file_path="/path.pdf")

        assert result == 42
        report_repo_mock.create_report.assert_called_once_with(1, 1, "/path.pdf")

    def test_create_report_invalid_order_id_raises(self, report_service):
        """Некорректный order_id — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID заказа"):
            report_service.create_report(0, 1)

    def test_create_report_invalid_employee_id_raises(self, report_service):
        """Некорректный employee_id — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID сотрудника"):
            report_service.create_report(1, 0)

    def test_get_next_report_number(self, report_service, report_repo_mock):
        """Следующий номер отчёта."""
        report_repo_mock.get_next_report_number.return_value = 100

        result = report_service.get_next_report_number()

        assert result == 100

    def test_get_report_by_path(self, report_service, report_repo_mock):
        """Поиск отчёта по пути."""
        report_repo_mock.get_report_by_path.return_value = {"report_id": 1}

        result = report_service.get_report_by_path("/path.pdf")

        assert result["report_id"] == 1

    def test_get_report_by_path_empty_raises(self, report_service):
        """Пустой путь — ValueError."""
        with pytest.raises(ValueError, match="Путь к файлу обязателен"):
            report_service.get_report_by_path("")

    def test_delete_report(self, report_service, report_repo_mock):
        """Удаление отчёта."""
        report_service.delete_report(1)

        report_repo_mock.delete_report.assert_called_once_with(1)

    def test_delete_report_invalid_id_raises(self, report_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID отчёта"):
            report_service.delete_report(0)

    def test_update_report_path(self, report_service, report_repo_mock):
        """Обновление пути к файлу."""
        report_service.update_report_path(1, "/new/path.pdf")

        report_repo_mock.update_report_path.assert_called_once_with(1, "/new/path.pdf")

    def test_update_report_path_invalid_id_raises(self, report_service):
        """Некорректный ID — ValueError."""
        with pytest.raises(ValueError, match="Некорректный ID отчёта"):
            report_service.update_report_path(0, "/path")

    def test_update_report_path_empty_raises(self, report_service):
        """Пустой путь — ValueError."""
        with pytest.raises(ValueError, match="Путь к файлу обязателен"):
            report_service.update_report_path(1, "")


class TestReportServiceFileOperations:
    """Тесты работы с файлами (open/print)."""

    def test_open_file_success(self, report_service):
        """Успешное открытие файла."""
        with patch("services.report_service.open_file") as mock_open:
            report_service.open_file("/path.pdf")
            mock_open.assert_called_once_with("/path.pdf")

    def test_open_file_error_logged_and_raised(self, report_service, caplog):
        """Ошибка открытия — логируется и пробрасывается."""
        with patch("services.report_service.open_file", side_effect=OSError("Permission denied")):
            with pytest.raises(OSError):
                report_service.open_file("/path.pdf")

        assert "Не удалось открыть файл" in caplog.text

    def test_print_file_success(self, report_service):
        """Успешная печать."""
        with patch("services.report_service.print_file") as mock_print:
            report_service.print_file("/path.pdf")
            mock_print.assert_called_once_with("/path.pdf")

    def test_print_file_error_logged_and_raised(self, report_service, caplog):
        """Ошибка печати — логируется и пробрасывается."""
        with patch("services.report_service.print_file", side_effect=OSError("Printer error")):
            with pytest.raises(OSError):
                report_service.print_file("/path.pdf")

        assert "Не удалось отправить на печать" in caplog.text