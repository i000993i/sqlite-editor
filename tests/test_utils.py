import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from functions.utils import (
    validate_table_name,
    validate_column_name,
    validate_order_by,
    format_size,
    truncate_string,
    safe_table_name,
)


def test_validate_table_name():
    assert validate_table_name("users") is True
    assert validate_table_name("_private") is True
    assert validate_table_name("table123") is True
    assert validate_table_name("") is False
    assert validate_table_name(None) is False
    assert validate_table_name("123abc") is False
    assert validate_table_name("table name") is False
    assert validate_table_name("drop;users") is False


def test_validate_column_name():
    assert validate_column_name("id") is True
    assert validate_column_name("user_email") is True
    assert validate_column_name("") is False
    assert validate_column_name(None) is False
    assert validate_column_name("col name") is False
    assert validate_column_name("1abc") is False


def test_validate_order_by():
    assert validate_order_by("id") is True
    assert validate_order_by("name ASC") is True
    assert validate_order_by("name DESC") is True
    assert validate_order_by("") is False
    assert validate_order_by(None) is False
    assert validate_order_by("id INJECT") is False
    assert validate_order_by("a b c") is False


def test_format_size():
    assert "Б" in format_size(100)
    assert "КБ" in format_size(2048)
    assert "МБ" in format_size(1048576 * 2)
    assert "ГБ" in format_size(1073741824 * 2)
    assert "ТБ" in format_size(1099511627776 * 2)


def test_truncate_string():
    assert truncate_string("hello", 10) == "hello"
    assert truncate_string("hello world", 10) == "hello w..."
    assert truncate_string("", 5) == ""


def test_safe_table_name():
    assert safe_table_name("users") == "users"
    assert safe_table_name("table name!") == "table_name_"
    assert safe_table_name("") == ""
