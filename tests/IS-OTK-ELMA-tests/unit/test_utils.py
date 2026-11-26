"""Unit-тесты для утилит."""

from __future__ import annotations

from datetime import date, datetime
from unittest.mock import patch, MagicMock

import pytest

from utils.formatting import format_date
from utils.files import open_file, print_file
from utils.passwords import generate_password


class TestFormatting:
    """Тесты format_date."""

    def test_format_date_none(self):
        """None -> пустая строка."""
        assert format_date(None) == ""

    def test_format_date_datetime(self):
        """datetime -> ДД.ММ.ГГГГ."""
        dt = datetime(2024, 1, 15, 14, 30)
        assert format_date(dt) == "15.01.2024"

    def test_format_date_date(self):
        """date -> ДД.ММ.ГГГГ."""
        d = date(2024, 12, 31)
        assert format_date(d) == "31.12.2024"

    def test_format_date_string(self):
        """Строка возвращается как есть."""
        assert format_date("2024-01-15") == "2024-01-15"

    def test_format_date_int(self):
        """Число конвертируется в строку."""
        assert format_date(123) == "123"


class TestPasswords:
    """Тесты generate_password."""

    def test_generate_password_default_length(self):
        """Длина по умолчанию 8."""
        pwd = generate_password()
        assert len(pwd) == 8

    def test_generate_password_custom_length(self):
        """Заданная длина."""
        pwd = generate_password(12)
        assert len(pwd) == 12

    def test_generate_password_alphanumeric(self):
        """Только буквы и цифры."""
        pwd = generate_password(20)
        assert all(c.isalnum() for c in pwd)

    def test_generate_password_min_length_4(self):
        """Минимум 4 символа."""
        pwd = generate_password(4)
        assert len(pwd) == 4

    def test_generate_password_too_short_raises(self):
        """Меньше 4 — ValueError."""
        with pytest.raises(ValueError, match="не меньше 4 символов"):
            generate_password(3)

    def test_generate_password_different_each_call(self):
        """Каждый вызов даёт разный пароль."""
        pwd1 = generate_password(10)
        pwd2 = generate_password(10)
        # Вероятность совпадения крайне мала
        assert pwd1 != pwd2


class TestFiles:
    """Тесты open_file / print_file."""

    def test_open_file_not_exists_raises(self):
        """Несуществующий файл — FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            open_file("/nonexistent/path.pdf")

    def test_open_file_empty_path_raises(self):
        """Пустой путь — FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            open_file("")

    @patch("utils.files.os.path.exists", return_value=True)
    @patch("utils.files.os.startfile")
    def test_open_file_windows(self, mock_startfile, mock_exists):
        """Windows: os.startfile."""
        with patch("utils.files.sys.platform", "win32"):
            open_file("C:/test/file.pdf")
            mock_startfile.assert_called_once_with("C:/test/file.pdf")

    @patch("utils.files.os.path.exists", return_value=True)
    @patch("utils.files.subprocess.Popen")
    def test_open_file_macos(self, mock_popen, mock_exists):
        """macOS: open."""
        with patch("utils.files.sys.platform", "darwin"):
            open_file("/test/file.pdf")
            mock_popen.assert_called_once_with(["open", "/test/file.pdf"])

    @patch("utils.files.os.path.exists", return_value=True)
    @patch("utils.files.subprocess.Popen")
    def test_open_file_linux(self, mock_popen, mock_exists):
        """Linux: xdg-open."""
        with patch("utils.files.sys.platform", "linux"):
            open_file("/test/file.pdf")
            mock_popen.assert_called_once_with(["xdg-open", "/test/file.pdf"])

    def test_print_file_not_exists_raises(self):
        """Несуществующий файл — FileNotFoundError."""
        with pytest.raises(FileNotFoundError, match="Файл не найден"):
            print_file("/nonexistent/path.pdf")

    @patch("utils.files.os.path.exists", return_value=True)
    @patch("utils.files.os.startfile")
    def test_print_file_windows(self, mock_startfile, mock_exists):
        """Windows: os.startfile с verb='print'."""
        with patch("utils.files.sys.platform", "win32"):
            print_file("C:/test/file.pdf")
            mock_startfile.assert_called_once_with("C:/test/file.pdf", "print")

    @patch("utils.files.os.path.exists", return_value=True)
    @patch("utils.files.subprocess.Popen")
    def test_print_file_linux(self, mock_popen, mock_exists):
        """Linux: lp."""
        with patch("utils.files.sys.platform", "linux"):
            print_file("/test/file.pdf")
            mock_popen.assert_called_once_with(["lp", "/test/file.pdf"])