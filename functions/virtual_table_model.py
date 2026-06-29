from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, QVariant, pyqtSignal, QThread
from PyQt6.QtWidgets import QApplication
from functions.logger import models_logger
from functions.async_manager import AsyncManager, WorkerThread
from typing import Callable, Optional, List, Tuple

class VirtualTableModel(QAbstractTableModel):
    
    page_loaded = pyqtSignal(int, int, int)
    search_started = pyqtSignal(str)
    search_finished = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, db_connection=None, page_size: int = 100):
        super().__init__()
        self.db_connection = db_connection
        self.db_manager = None
        self.page_size = page_size
        
        self._current_table = None
        self._current_page = 0
        self._total_rows = 0
        self._columns = []
        self._data: List[list] = []
        self._rowids: List[int] = []
        self._primary_key = None
        
        self._search_mode = False
        self._search_text = ""
        self._search_results: List[list] = []
        self._search_rowids: List[int] = []
        self._search_total = 0
        
        self._page_cache = {}
        self._max_cached_pages = 20
        
        self._async_manager = AsyncManager()
        self._loading = False
        
        self._update_callback = None
        self._editable = False
    
    def _extract_rowids(self, data, columns):
        if not data:
            return [], [], columns or []
        rows = [list(row) for row in data]
        if columns and columns[0] == 'rowid':
            rowids = [row[0] for row in rows]
            clean_data = [row[1:] for row in rows]
            clean_columns = columns[1:]
            return rowids, clean_data, clean_columns
        return [], rows, columns or []
    
    def set_update_callback(self, callback: Callable):
        self._update_callback = callback
    
    def set_editable(self, editable: bool):
        self._editable = editable
    
    def set_connection(self, db_manager):
        self.db_manager = db_manager
        self.db_connection = db_manager.connection if db_manager else None
    
    def set_data(self, data, columns, total_rows=None):
        rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
        self.beginResetModel()
        self._data = clean_data
        self._rowids = rowids
        self._columns = clean_columns
        self._total_rows = total_rows if total_rows is not None else len(clean_data)
        self.endResetModel()
    
    def get_rowid(self, row: int) -> int:
        if self._search_mode:
            if 0 <= row < len(self._search_rowids):
                return self._search_rowids[row]
        else:
            if 0 <= row < len(self._rowids):
                return self._rowids[row]
        return None
    
    def get_column_index(self, column_name: str) -> int:
        for i, col in enumerate(self._columns):
            if col == column_name:
                return i
        return None
    
    def get_primary_key(self) -> str:
        return self._primary_key
    
    def load_table(self, table_name: str, order_by: str = None, 
                   progress_callback: Callable = None) -> WorkerThread:
        if not self.db_manager:
            self.error_occurred.emit("Нет подключения к БД")
            return None
        
        self.beginResetModel()
        self._current_table = table_name
        self._current_page = 0
        self._columns = []
        self._data = []
        self._rowids = []
        self._total_rows = 0
        self._search_mode = False
        self._page_cache.clear()
        self.endResetModel()
        
        def load_task():
            success, data, columns, total, error = self.db_manager.get_table_page(
                table_name,
                offset=0,
                limit=self.page_size,
                order_by=order_by,
                progress_callback=progress_callback
            )
            
            if success:
                rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
                self._rowids = rowids
                self._columns = clean_columns
                self._data = clean_data
                self._total_rows = total
                
                schema = self.db_manager.get_table_schema(table_name)
                if schema:
                    self._primary_key = schema.get('primary_key')
                
                models_logger.info(f"Таблица {table_name}: {total} строк, {len(clean_columns)} колонок")
            
            return (success, data, columns, total, error)
        
        def on_finished(result):
            success, data, columns, total, error = result
            if success:
                rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
                self.beginResetModel()
                self._rowids = rowids
                self._columns = clean_columns
                self._data = clean_data
                self._total_rows = total
                self.endResetModel()
                self.page_loaded.emit(0, total, len(clean_columns))
            else:
                self.error_occurred.emit(error or "Ошибка загрузки таблицы")
        
        def on_error(error_msg):
            self.error_occurred.emit(error_msg)
        
        return self._async_manager.execute_async(load_task, on_finished, on_error)
    
    def load_page(self, page: int, progress_callback: Callable = None) -> WorkerThread:
        if self._loading or not self._current_table:
            return None
        
        if self._search_mode:
            return None
        
        if page in self._page_cache:
            cached = self._page_cache[page]
            self.beginResetModel()
            self._current_page = page
            self._data = cached['data']
            self._rowids = cached['rowids']
            self.endResetModel()
            self.page_loaded.emit(page, self._total_rows, len(self._columns))
            return None
        
        self._loading = True
        
        offset = page * self.page_size
        
        def load_task():
            return self.db_manager.get_table_page(
                self._current_table,
                offset=offset,
                limit=self.page_size,
                progress_callback=progress_callback
            )
        
        def on_finished(result):
            self._loading = False
            success, data, columns, total, error = result
            
            if success:
                rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
                self.beginResetModel()
                self._current_page = page
                self._rowids = rowids
                self._data = clean_data
                self._total_rows = total
                
                self._cache_page(page, clean_data, rowids)
                
                self.endResetModel()
                self.page_loaded.emit(page, total, len(clean_columns))
            else:
                self.error_occurred.emit(error or "Ошибка загрузки страницы")
        
        def on_error(error_msg):
            self._loading = False
            self.error_occurred.emit(error_msg)
        
        return self._async_manager.execute_async(load_task, on_finished, on_error)
    
    def _cache_page(self, page: int, data: list, rowids: list):
        self._page_cache[page] = {'data': data, 'rowids': rowids}
        
        if len(self._page_cache) > self._max_cached_pages:
            oldest_page = min(self._page_cache.keys())
            del self._page_cache[oldest_page]
    
    def search(self, search_text: str, limit: int = 1000,
               progress_callback: Callable = None) -> WorkerThread:
        if not self._current_table or not self.db_manager:
            self.error_occurred.emit("Нет таблицы или подключения")
            return None
        
        self.beginResetModel()
        self._search_mode = True
        self._search_text = search_text
        self._search_results = []
        self._search_rowids = []
        self._search_total = 0
        self.endResetModel()
        
        self.search_started.emit(search_text)
        
        def search_task():
            return self.db_manager.search_table(
                self._current_table,
                search_text,
                limit=limit,
                progress_callback=progress_callback
            )
        
        def on_finished(result):
            success, data, columns, total, error = result
            
            if success:
                rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
                self.beginResetModel()
                self._search_rowids = rowids
                self._search_results = clean_data
                self._search_total = total
                self.endResetModel()
                self.search_finished.emit(total)
            else:
                self.error_occurred.emit(error or "Ошибка поиска")
                self._search_mode = False
        
        def on_error(error_msg):
            self._search_mode = False
            self.error_occurred.emit(error_msg)
        
        return self._async_manager.execute_async(search_task, on_finished, on_error)
    
    def clear_search(self):
        if self._search_mode:
            self.beginResetModel()
            self._search_mode = False
            self._search_text = ""
            self._search_results = []
            self._search_rowids = []
            self.endResetModel()
    
    def cancel(self):
        self._async_manager.cancel_current()
    
    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        
        if self._search_mode:
            return len(self._search_results)
        return len(self._data)
    
    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)
    
    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole) -> QVariant:
        if not index.isValid():
            return QVariant()
        
        row = index.row()
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole or role == Qt.ItemDataRole.EditRole:
            if self._search_mode:
                if row < len(self._search_results) and col < len(self._search_results[row]):
                    return str(self._search_results[row][col])
            else:
                if row < len(self._data) and col < len(self._data[row]):
                    return str(self._data[row][col])
        
        return QVariant()
    
    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole) -> QVariant:
        if role == Qt.ItemDataRole.DisplayRole:
            if orientation == Qt.Orientation.Horizontal:
                if 0 <= section < len(self._columns):
                    return self._columns[section]
            else:
                return str(section + 1)
        return QVariant()
    
    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        
        flags = super().flags(index)
        if self._editable and self._update_callback:
            return flags | Qt.ItemFlag.ItemIsEditable
        return flags | Qt.ItemFlag.ItemIsSelectable
    
    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or not self._update_callback:
            return False
        
        if role == Qt.ItemDataRole.EditRole:
            row = index.row()
            col = index.column()
            
            if self._search_mode:
                if row >= len(self._search_results):
                    return False
                old_value = self._search_results[row][col]
                self._search_results[row][col] = value
                rowid = self._search_rowids[row] if row < len(self._search_rowids) else None
            else:
                if row >= len(self._data):
                    return False
                old_value = self._data[row][col]
                self._data[row][col] = value
                rowid = self._rowids[row] if row < len(self._rowids) else None
            
            if rowid is not None:
                col_name = self._columns[col]
                self._update_callback(col_name, value, rowid)
            
            self.dataChanged.emit(index, index, [role])
            return True
        
        return False
    
    def is_search_mode(self) -> bool:
        return self._search_mode
    
    def get_columns(self) -> list:
        return list(self._columns)

    def get_current_table(self) -> str:
        return self._current_table
    
    def get_total_rows(self) -> int:
        if self._search_mode:
            return self._search_total
        return self._total_rows
    
    def get_visible_rows(self) -> int:
        if self._search_mode:
            return len(self._search_results)
        return len(self._data)
    
    def get_current_page(self) -> int:
        return self._current_page
    
    def is_loading(self) -> bool:
        return self._loading or self._async_manager.is_busy()
