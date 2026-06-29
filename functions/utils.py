import os
import re
from functions.logger import utils_logger

TABLE_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')
COLUMN_NAME_PATTERN = re.compile(r'^[a-zA-Z_][a-zA-Z0-9_]*$')

def validate_table_name(name):
    if not name or not isinstance(name, str):
        return False
    return bool(TABLE_NAME_PATTERN.match(name))

def validate_column_name(name):
    if not name or not isinstance(name, str):
        return False
    return bool(COLUMN_NAME_PATTERN.match(name))

def validate_order_by(order_by):
    if not order_by or not isinstance(order_by, str):
        return False
    cleaned = order_by.strip()
    if not cleaned:
        return False
    parts = cleaned.split()
    if len(parts) > 2:
        return False
    col_name = parts[0].strip('"')
    if not validate_column_name(col_name):
        return False
    if len(parts) == 2 and parts[1].upper() not in ('ASC', 'DESC'):
        return False
    return True

def format_size(size):
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ТБ"

def truncate_string(text, max_length=100):
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def safe_table_name(name):
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)