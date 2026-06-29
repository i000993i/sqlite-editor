from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker
from functions.logger import utils_logger
from functions.utils import validate_table_name
from typing import Callable, Any, Optional
import traceback

class WorkerThread(QThread):
    finished = pyqtSignal(bool, object, str)
    progress = pyqtSignal(int, str)
    
    def __init__(self, task: Callable, *args, **kwargs):
        super().__init__()
        self.task = task
        self.args = args
        self.kwargs = kwargs
        self._cancelled = False
    
    def run(self):
        try:
            if self._cancelled:
                return
            result = self.task(*self.args, **self.kwargs)
            if not self._cancelled:
                self.finished.emit(True, result, "Операция завершена")
        except Exception as e:
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            utils_logger.error(f"Ошибка в рабочем потоке: {error_msg}")
            self.finished.emit(False, None, str(e))
    
    def cancel(self):
        """Попытка отменить выполнение"""
        self._cancelled = True
    
    @property
    def cancelled(self):
        return self._cancelled


class AsyncManager:
    """Менеджер для управления асинхронными операциями"""
    
    def __init__(self):
        self._current_thread: Optional[WorkerThread] = None
        self._mutex = QMutex()
    
    def execute_async(self, task: Callable, on_finished: Callable = None, 
                      on_error: Callable = None, progress_callback: Callable = None) -> WorkerThread:
        """
        Выполнить задачу в отдельном потоке
        
        Args:
            task: Функция для выполнения
            on_finished: Колбэк при успешном завершении (result, message)
            on_error: Колбэк при ошибке (error_message)
            progress_callback: Колбэк для прогресса (percent, message)
            
        Returns:
            WorkerThread - ссылку на поток для управления
        """
        # Завершаем предыдущий поток если есть
        self.cancel_current()
        
        thread = WorkerThread(task)
        
        def on_task_finished(success: bool, result: Any, message: str):
            if success:
                if on_finished:
                    on_finished(result)
            else:
                if on_error:
                    on_error(message)
                else:
                    utils_logger.error(f"Асинхронная операция завершилась с ошибкой: {message}")
            
            # Освобождаем ссылку
            with QMutexLocker(self._mutex):
                self._current_thread = None
        
        thread.finished.connect(on_task_finished)
        
        if progress_callback:
            thread.progress.connect(progress_callback)
        
        # Сохраняем ссылку и запускаем
        with QMutexLocker(self._mutex):
            self._current_thread = thread
        
        thread.start()
        return thread
    
    def cancel_current(self):
        """Отменить текущую асинхронную операцию"""
        with QMutexLocker(self._mutex):
            if self._current_thread and self._current_thread.isRunning():
                self._current_thread.cancel()
                self._current_thread.wait(1000)  # Ждём 1 сек
                if self._current_thread.isRunning():
                    utils_logger.warning("Поток не завершился за 1с, продолжаем ждать")
                    self._current_thread.wait(2000)
                self._current_thread = None
    
    def is_busy(self) -> bool:
        """Проверить занят ли менеджер"""
        with QMutexLocker(self._mutex):
            return self._current_thread is not None and self._current_thread.isRunning()


class SchemaCache:
    """Кэш схемы базы данных"""
    
    def __init__(self):
        self._tables = None
        self._table_info = {}  # table_name -> columns info
        self._table_indexes = {}  # table_name -> indexes
        self._table_foreign_keys = {}  # table_name -> foreign keys
        self._total_rows = {}  # table_name -> row count
        self._cached = False
    
    def clear(self):
        """Очистить кэш"""
        self._tables = None
        self._table_info.clear()
        self._table_indexes.clear()
        self._table_foreign_keys.clear()
        self._total_rows.clear()
        self._cached = False
        utils_logger.info("Кэш схемы базы данных очищен")
    
    def is_valid(self) -> bool:
        """Проверить валидность кэша"""
        return self._cached and self._tables is not None
    
    def get_tables(self):
        """Получить список таблиц из кэша"""
        return self._tables if self._cached else []
    
    def get_table_info(self, table_name: str):
        """Получить информацию о таблице из кэша"""
        return self._table_info.get(table_name)
    
    def get_table_indexes(self, table_name: str):
        """Получить индексы таблицы из кэша"""
        return self._table_indexes.get(table_name, [])
    
    def get_table_foreign_keys(self, table_name: str):
        """Получить внешние ключи таблицы из кэша"""
        return self._table_foreign_keys.get(table_name, [])
    
    def get_row_count(self, table_name: str):
        """Получить количество строк из кэша"""
        return self._total_rows.get(table_name)
    
    def set_tables(self, tables: list):
        """Сохранить список таблиц в кэш"""
        self._tables = tables
        self._cached = True
    
    def set_table_info(self, table_name: str, info: list):
        """Сохранить информацию о таблице в кэш"""
        self._table_info[table_name] = info
    
    def set_table_indexes(self, table_name: str, indexes: list):
        """Сохранить индексы таблицы в кэш"""
        self._table_indexes[table_name] = indexes
    
    def set_table_foreign_keys(self, table_name: str, fks: list):
        """Сохранить внешние ключи таблицы в кэш"""
        self._table_foreign_keys[table_name] = fks
    
    def set_row_count(self, table_name: str, count: int):
        """Сохранить количество строк в кэш"""
        self._total_rows[table_name] = count
    
    def load_full_schema(self, db_connection):
        """
        Загрузить полную схему базы данных
        
        Returns:
            dict: {tables: [], table_info: {}, indexes: {}, foreign_keys: {}, row_counts: {}}
        """
        if not db_connection:
            return None
        
        try:
            cursor = db_connection.cursor()
            
            # Получаем все таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            table_names = [row[0] for row in cursor.fetchall() if validate_table_name(row[0])]
            
            tables_data = []
            table_info = {}
            table_indexes = {}
            table_foreign_keys = {}
            row_counts = {}
            
            for table_name in table_names:
                # Информация о колонках
                cursor.execute(f"PRAGMA table_info(\"{table_name}\");")
                columns = cursor.fetchall()
                table_info[table_name] = columns
                
                # Индексы
                cursor.execute(f"PRAGMA index_list(\"{table_name}\");")
                indexes = cursor.fetchall()
                table_indexes[table_name] = indexes
                
                # Внешние ключи
                cursor.execute(f"PRAGMA foreign_key_list(\"{table_name}\");")
                fks = cursor.fetchall()
                table_foreign_keys[table_name] = fks
                
                # Количество строк
                cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                count = cursor.fetchone()[0]
                row_counts[table_name] = count
                
                tables_data.append((table_name, count))
            
            # Сохраняем в кэш
            self.set_tables(tables_data)
            for name, info in table_info.items():
                self.set_table_info(name, info)
            for name, idx in table_indexes.items():
                self.set_table_indexes(name, idx)
            for name, fk in table_foreign_keys.items():
                self.set_table_foreign_keys(name, fk)
            for name, count in row_counts.items():
                self.set_row_count(name, count)
            
            utils_logger.info(f"Схема БД загружена: {len(tables_data)} таблиц")
            
            return {
                'tables': tables_data,
                'table_info': table_info,
                'indexes': table_indexes,
                'foreign_keys': table_foreign_keys,
                'row_counts': row_counts
            }
            
        except Exception as e:
            utils_logger.error(f"Ошибка загрузки схемы БД: {e}")
            return None



