import traceback
from typing import Callable, Any, Optional

from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QMutexLocker

from functions.logger import utils_logger
from functions.utils import validate_table_name


class WorkerThread(QThread):
    finished = pyqtSignal(bool, object, str)    # success, result, message
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
                self.finished.emit(True, result, "OK")
        except Exception as e:
            msg = f"{e}\n{traceback.format_exc()}"
            utils_logger.error(f"Ошибка в WorkerThread: {msg}")
            self.finished.emit(False, None, str(e))

    def cancel(self):
        self._cancelled = True

    @property
    def cancelled(self):
        return self._cancelled


class AsyncManager:

    def __init__(self):
        self._current_thread: Optional[WorkerThread] = None
        self._mutex = QMutex()
        self._db_connection = None      # для interrupt()

    def set_db_connection(self, conn):
        self._db_connection = conn

    def execute_async(self, task: Callable,
                      on_finished: Callable | None = None,
                      on_error: Callable | None = None,
                      progress_callback: Callable | None = None
                      ) -> WorkerThread:
        self.cancel_current()
        thread = WorkerThread(task)

        def _finished(success, result, message):
            if success:
                if on_finished:
                    on_finished(result)
            else:
                if on_error:
                    on_error(message)
                else:
                    utils_logger.error(f"async: {message}")
            with QMutexLocker(self._mutex):
                self._current_thread = None

        thread.finished.connect(_finished)
        if progress_callback:
            thread.progress.connect(progress_callback)

        with QMutexLocker(self._mutex):
            self._current_thread = thread

        thread.start()
        return thread

    def cancel_current(self):
        with QMutexLocker(self._mutex):
            t = self._current_thread
            if t and t.isRunning():
                t.cancel()
                # interrupt активного SQL, если есть соединение
                if self._db_connection is not None:
                    try:
                        self._db_connection.interrupt()
                    except Exception:
                        pass
                if not t.wait(3000):
                    utils_logger.warning("Поток не завершился за 3 с")
                self._current_thread = None

    def is_busy(self) -> bool:
        with QMutexLocker(self._mutex):
            return self._current_thread is not None and self._current_thread.isRunning()


class SchemaCache:

    def __init__(self):
        self._tables = None
        self._table_info = {}
        self._table_indexes = {}
        self._table_foreign_keys = {}
        self._total_rows = {}
        self._cached = False

    def clear(self):
        self._tables = None
        self._table_info.clear()
        self._table_indexes.clear()
        self._table_foreign_keys.clear()
        self._total_rows.clear()
        self._cached = False

    def is_valid(self) -> bool:
        return self._cached and self._tables is not None

    def get_tables(self):
        return self._tables if self._cached else []

    def get_table_info(self, table_name):
        return self._table_info.get(table_name)

    def set_tables(self, tables):
        self._tables = tables
        self._cached = True

    def set_table_info(self, name, info):
        self._table_info[name] = info

    def load_full_schema(self, db_connection):
        if not db_connection:
            return None
        try:
            cur = db_connection.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            names = [r[0] for r in cur.fetchall() if validate_table_name(r[0])]

            tables = []
            for name in names:
                cur.execute(f'PRAGMA table_info("{name}")')
                self._table_info[name] = cur.fetchall()

                cur.execute(f'PRAGMA index_list("{name}")')
                self._table_indexes[name] = cur.fetchall()

                cur.execute(f'PRAGMA foreign_key_list("{name}")')
                self._table_foreign_keys[name] = cur.fetchall()

                cur.execute(f'SELECT COUNT(*) FROM "{name}"')
                cnt = cur.fetchone()[0]
                self._total_rows[name] = cnt
                tables.append((name, cnt))

            self.set_tables(tables)
            utils_logger.info(f"Схема БД: {len(tables)} таблиц")
            return {
                "tables": tables,
                "table_info": self._table_info,
                "indexes": self._table_indexes,
                "foreign_keys": self._table_foreign_keys,
                "row_counts": self._total_rows,
            }
        except Exception as e:
            utils_logger.error(f"load_full_schema: {e}")
            return None