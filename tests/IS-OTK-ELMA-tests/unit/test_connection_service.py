"""Unit-тесты для ConnectionService."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from services.connection_service import ConnectionService


class TestConnectionService:
    """Тесты ConnectionService (мокируем db.connection)."""

    def test_is_db_available_true(self, connection_service):
        """БД доступна."""
        with patch("services.connection_service._check_db", return_value=(True, None)):
            result = connection_service.is_db_available()
            assert result is True

    def test_is_db_available_false(self, connection_service):
        """БД недоступна."""
        with patch("services.connection_service._check_db", return_value=(False, "Connection refused")):
            result = connection_service.is_db_available()
            assert result is False

    def test_check_db_returns_tuple(self, connection_service):
        """check_db возвращает кортеж."""
        with patch("services.connection_service._check_db", return_value=(True, None)):
            ok, error = connection_service.check_db()
            assert ok is True
            assert error is None

    def test_connect_returns_connection(self, connection_service):
        """connect возвращает соединение."""
        mock_conn = MagicMock()
        with patch("services.connection_service._connect", return_value=mock_conn):
            result = connection_service.connect()
            assert result is mock_conn

    def test_get_config_info(self, connection_service):
        """Получение информации о конфигурации."""
        with patch("services.connection_service._get_config_info", return_value="host=localhost;db=test"):
            result = connection_service.get_config_info()
            assert "host=localhost" in result

    def test_ensure_schema(self, connection_service):
        """Миграция схемы."""
        with patch("services.connection_service._ensure_schema", return_value="Schema OK"):
            result = connection_service.ensure_schema()
            assert result == "Schema OK"

    def test_connect_with_retry_success(self, connection_service):
        """Подключение с повторами — успех."""
        with patch("services.connection_service._connect_with_retry", return_value=True):
            result = connection_service.connect_with_retry(max_attempts=3, delay=0.5)
            assert result is True

    def test_connect_with_retry_failure(self, connection_service):
        """Подключение с повторами — неудача."""
        with patch("services.connection_service._connect_with_retry", return_value=False):
            result = connection_service.connect_with_retry(max_attempts=3, delay=0.5)
            assert result is False

    def test_close(self, connection_service):
        """Закрытие соединения."""
        with patch("services.connection_service._close_connection") as mock_close:
            connection_service.close()
            mock_close.assert_called_once()