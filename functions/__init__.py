"""
Пакет functions.
Ленивый __init__: НЕ импортирует подмодули, чтобы ошибка в одном
модуле не ломала доступ к functions.logger / functions.paths / functions.utils.
"""

__all__ = [
    "logger", "paths", "utils", "styles",
    "database", "import_export", "async_manager",
    "virtual_table_model", "table_viewer_virtual",
    "sql_editor", "table_designer", "data_visualizer",
    "data_analysis",
]