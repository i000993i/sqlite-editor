import os

def format_size(size):
    """Форматирование размера файла"""
    for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ТБ"

def truncate_string(text, max_length=100):
    """Обрезать строку до указанной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."

def safe_table_name(name):
    """Безопасное имя таблицы"""
    import re
    return re.sub(r'[^a-zA-Z0-9_]', '_', name)