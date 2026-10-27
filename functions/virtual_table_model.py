from PyQt6.QtCore import QAbstractTableModel, QModelIndex, Qt, pyqtSignal
from functions.logger import models_logger
from functions.async_manager import AsyncManager, WorkerThread
from typing import Callable, List


class VirtualTableModel(QAbstractTableModel):

    page_loaded = pyqtSignal(int, int, int)          # page, total_rows, columns
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
        self._columns: List[str] = []
        self._data: List[list] = []
        self._rowids: List[int] = []
        self._primary_key = None

        self._search_mode = False
        self._search_text = ""
        self._search_results: List[list] = []
        self._search_rowids: List[int] = []
        self._search_total = 0

        self._page_cache: dict[int, dict] = {}
        self._max_cached_pages = 20

        self._async_manager = AsyncManager()
        self._loading = False

        self._update_callback: Callable | None = None
        self._editable = False

    # ---------- helpers ----------

    def _extract_rowids(self, data, columns):
        if not data:
            return [], [], columns or []
        rows = [list(row) for row in data]
        if columns and columns[0] == "rowid":
            return ([r[0] for r in rows], [r[1:] for r in rows], list(columns[1:]))
        return [], rows, list(columns or [])

    def set_update_callback(self, callback: Callable | None):
        """callback(col_name, value, rowid) -> (success: bool, error: str|None)"""
        self._update_callback = callback

    def set_editable(self, editable: bool):
        self._editable = editable
        self.layoutChanged.emit()

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
        self._search_mode = False
        self.endResetModel()

    # ---------- accessors ----------

    def get_rowid(self, row: int):
        if self._search_mode:
            if 0 <= row < len(self._search_rowids):
                return self._search_rowids[row]
        else:
            if 0 <= row < len(self._rowids):
                return self._rowids[row]
        return None

    def get_columns(self) -> list:
        return list(self._columns)

    def get_current_table(self):
        return self._current_table

    def get_total_rows(self) -> int:
        return self._search_total if self._search_mode else self._total_rows

    def get_visible_rows(self) -> int:
        return len(self._search_results) if self._search_mode else len(self._data)

    def get_current_page(self) -> int:
        return self._current_page

    def is_search_mode(self) -> bool:
        return self._search_mode

    def is_loading(self) -> bool:
        return self._loading or self._async_manager.is_busy()

    # ---------- async loading ----------

    def load_table(self, table_name: str, order_by: str | None = None,
                   progress_callback: Callable | None = None) -> WorkerThread | None:
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
            return self.db_manager.get_table_page(
                table_name, offset=0, limit=self.page_size,
                order_by=order_by, progress_callback=progress_callback,
            )

        def on_finished(result):
            success, data, columns, total, error = result
            if not success:
                self.error_occurred.emit(error or "Ошибка загрузки таблицы")
                return
            rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
            schema = self.db_manager.get_table_schema(table_name)
            if schema:
                self._primary_key = schema.get("primary_key")
            self.beginResetModel()
            self._rowids = rowids
            self._columns = clean_columns
            self._data = clean_data
            self._total_rows = total
            self.endResetModel()
            models_logger.info(f"{table_name}: {total} строк, {len(clean_columns)} колонок")
            self.page_loaded.emit(0, total, len(clean_columns))

        def on_error(msg):
            self.error_occurred.emit(msg)

        return self._async_manager.execute_async(load_task, on_finished, on_error)

    def load_page(self, page: int, progress_callback: Callable | None = None) -> WorkerThread | None:
        if self._loading or not self._current_table or self._search_mode:
            return None

        if page in self._page_cache:
            cached = self._page_cache[page]
            self.beginResetModel()
            self._current_page = page
            self._data = cached["data"]
            self._rowids = cached["rowids"]
            self.endResetModel()
            self.page_loaded.emit(page, self._total_rows, len(self._columns))
            return None

        self._loading = True
        offset = page * self.page_size

        def load_task():
            return self.db_manager.get_table_page(
                self._current_table, offset=offset, limit=self.page_size,
                progress_callback=progress_callback,
            )

        def on_finished(result):
            self._loading = False
            success, data, columns, total, error = result
            if not success:
                self.error_occurred.emit(error or "Ошибка загрузки страницы")
                return
            rowids, clean_data, clean_columns = self._extract_rowids(data, columns)
            self.beginResetModel()
            self._current_page = page
            self._rowids = rowids
            self._data = clean_data
            self._total_rows = total
            self._cache_page(page, clean_data, rowids)
            self.endResetModel()
            self.page_loaded.emit(page, total, len(clean_columns))

        def on_error(msg):
            self._loading = False
            self.error_occurred.emit(msg)

        return self._async_manager.execute_async(load_task, on_finished, on_error)

    def _cache_page(self, page: int, data: list, rowids: list):
        self._page_cache[page] = {"data": data, "rowids": rowids}
        if len(self._page_cache) > self._max_cached_pages:
            del self._page_cache[min(self._page_cache.keys())]

    def search(self, search_text: str, limit: int = 1000,
               progress_callback: Callable | None = None) -> WorkerThread | None:
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
                self._current_table, search_text, limit=limit,
                progress_callback=progress_callback,
            )

        def on_finished(result):
            success, data, columns, total, error = result
            if not success:
                self._search_mode = False
                self.error_occurred.emit(error or "Ошибка поиска")
                return
            rowids, clean_data, _ = self._extract_rowids(data, columns)
            self.beginResetModel()
            self._search_rowids = rowids
            self._search_results = clean_data
            self._search_total = total
            self.endResetModel()
            self.search_finished.emit(total)

        def on_error(msg):
            self._search_mode = False
            self.error_occurred.emit(msg)

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

    # ---------- Qt API ----------

    def rowCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._search_results) if self._search_mode else len(self._data)

    def columnCount(self, parent=QModelIndex()) -> int:
        if parent.isValid():
            return 0
        return len(self._columns)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            row, col = index.row(), index.column()
            src = self._search_results if self._search_mode else self._data
            if 0 <= row < len(src) and 0 <= col < len(src[row]):
                v = src[row][col]
                return "" if v is None else str(v)
        return None

    def headerData(self, section: int, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            if 0 <= section < len(self._columns):
                return self._columns[section]
            return None
        return str(section + 1)

    def flags(self, index: QModelIndex):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        flags = Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEnabled
        if self._editable and self._update_callback and not self._search_mode:
            flags |= Qt.ItemFlag.ItemIsEditable
        return flags

    def setData(self, index: QModelIndex, value, role=Qt.ItemDataRole.EditRole) -> bool:
        if not index.isValid() or not self._update_callback or role != Qt.ItemDataRole.EditRole:
            return False
        if self._search_mode:
            return False  # правка отключена во время поиска

        row, col = index.row(), index.column()
        if row >= len(self._data):
            return False
        rowid = self._rowids[row] if row < len(self._rowids) else None
        if rowid is None:
            return False

        col_name = self._columns[col]
        # 1) сначала БД
        result = self._update_callback(col_name, value, rowid)
        success = isinstance(result, tuple) and result[0] is True
        if not success:
            err = result[1] if isinstance(result, tuple) else "неизвестная ошибка"
            models_logger.error(f"setData ошибка БД: {err}")
            return False
        # 2) потом модель
        self._data[row][col] = value
        self.dataChanged.emit(index, index, [role])
        return True