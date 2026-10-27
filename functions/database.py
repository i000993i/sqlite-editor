import sqlite3
import os
import threading
import shutil
from datetime import datetime
from typing import Callable
from functions.logger import db_logger
from functions.utils import validate_table_name, validate_column_name, validate_order_by


class DatabaseManager:
    """
    Потокобезопасная обёртка над SQLite.
    Все операции сериализуются через RLock (SQLite всё равно не даёт параллелизма
    на одном соединении, а так мы избегаем database is locked / гонок).
    """

    def __init__(self):
        self.connection: sqlite3.Connection | None = None
        self.current_db: str | None = None
        self.query_history: list = []
        self._lock = threading.RLock()

    # ---------- connect ----------

    def connect(self, db_path: str) -> bool:
        with self._lock:
            try:
                if self.connection:
                    self.connection.close()
                self.connection = sqlite3.connect(
                    db_path, check_same_thread=False, timeout=30.0,
                )
                self.connection.execute("PRAGMA journal_mode=WAL")
                self.connection.execute("PRAGMA foreign_keys=ON")
                self.connection.execute("PRAGMA synchronous=NORMAL")
                self.current_db = db_path
                db_logger.info(f"Подключение к БД: {db_path}")
                return True
            except Exception as e:
                db_logger.error(f"Ошибка подключения {db_path}: {e}")
                return False

    def create_database(self, db_path: str) -> bool:
        return self.connect(db_path)

    def close(self):
        with self._lock:
            if self.connection:
                self.connection.close()
                self.connection = None
                self.current_db = None

    # ---------- read ----------

    def get_tables(self):
        with self._lock:
            if not self.connection:
                return []
            cur = self.connection.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            names = [r[0] for r in cur.fetchall() if validate_table_name(r[0])]
            # COUNT(*) для больших таблиц медленный — можно кэшировать.
            return [(n, self._count(n)) for n in names]

    def get_table_names(self):
        with self._lock:
            if not self.connection:
                return []
            cur = self.connection.cursor()
            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            return [r[0] for r in cur.fetchall() if validate_table_name(r[0])]

    def _count(self, table_name: str) -> int:
        cur = self.connection.cursor()
        cur.execute(f'SELECT COUNT(*) FROM "{table_name}"')
        return cur.fetchone()[0]

    def get_table_page(self, table_name: str, offset=0, limit=100,
                       order_by=None, where_clause=None,
                       progress_callback: Callable = None) -> tuple:
        with self._lock:
            if not self.connection:
                return False, [], [], 0, "Нет подключения к БД"
            if not validate_table_name(table_name):
                return False, [], [], 0, "Неверное имя таблицы"
            try:
                cur = self.connection.cursor()
                safe_table = f'"{table_name}"'
                if progress_callback:
                    progress_callback(10, "Подсчёт строк...")
                cur.execute(f"SELECT COUNT(*) FROM {safe_table}")
                total = cur.fetchone()[0]

                if progress_callback:
                    progress_callback(30, "Загрузка данных...")
                sql = f"SELECT rowid, * FROM {safe_table}"
                if where_clause:
                    sql += f" WHERE {where_clause}"
                if order_by and validate_order_by(order_by):
                    sql += f" ORDER BY {order_by}"
                else:
                    sql += " ORDER BY ROWID"
                sql += f" LIMIT {int(limit)} OFFSET {int(offset)}"

                cur.execute(sql)
                data = cur.fetchall()
                columns = [d[0] for d in cur.description] if cur.description else []

                if progress_callback:
                    progress_callback(100, "Готово")
                return True, data, columns, total, None
            except Exception as e:
                db_logger.error(f"Ошибка загрузки {table_name}: {e}")
                return False, [], [], 0, str(e)

    def get_table_schema(self, table_name: str):
        with self._lock:
            if not self.connection or not validate_table_name(table_name):
                return None
            try:
                cur = self.connection.cursor()
                cur.execute(f'PRAGMA table_info("{table_name}")')
                cols, pk = [], None
                for c in cur.fetchall():
                    cols.append({
                        "name": c[1], "type": c[2] or "TEXT",
                        "notnull": bool(c[3]), "default": c[4],
                        "primary_key": bool(c[5]),
                    })
                    if c[5]:
                        pk = c[1]
                return {"columns": cols, "primary_key": pk, "has_rowid": True}
            except Exception as e:
                db_logger.error(f"Ошибка схемы {table_name}: {e}")
                return None

    def search_table(self, table_name, search_text, limit=1000,
                     progress_callback=None) -> tuple:
        with self._lock:
            if not self.connection or not validate_table_name(table_name):
                return False, [], [], 0, "Нет подключения или неверное имя таблицы"
            try:
                schema = self.get_table_schema(table_name)
                if not schema:
                    return False, [], [], 0, "Не удалось получить схему"
                text_cols = [c["name"] for c in schema["columns"]
                             if c["type"].upper().startswith(("TEXT", "VARCHAR", "CHAR", "CLOB"))]
                if not text_cols:
                    text_cols = [c["name"] for c in schema["columns"]]

                where = " OR ".join(f'"{c}" LIKE ?' for c in text_cols)
                pattern = f"%{search_text}%"

                cur = self.connection.cursor()
                if progress_callback:
                    progress_callback(10, "Подсчёт результатов...")
                cur.execute(f'SELECT COUNT(*) FROM "{table_name}" WHERE {where}',
                            [pattern] * len(text_cols))
                total = cur.fetchone()[0]

                if progress_callback:
                    progress_callback(40, "Загрузка результатов...")
                cur.execute(f'SELECT rowid, * FROM "{table_name}" WHERE {where} LIMIT ?',
                            [pattern] * len(text_cols) + [int(limit)])
                data = cur.fetchall()
                columns = [d[0] for d in cur.description] if cur.description else []

                if progress_callback:
                    progress_callback(100, "Готово")
                return True, data, columns, total, None
            except Exception as e:
                db_logger.error(f"Ошибка поиска {table_name}: {e}")
                return False, [], [], 0, str(e)

    # ---------- execute ----------

    def execute_query(self, query: str):
        with self._lock:
            if not self.connection:
                return False, "Нет подключения к БД", None
            try:
                self.query_history.append(
                    {"query": query, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")})
                cur = self.connection.cursor()
                cur.execute(query)
                if query.upper().strip().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
                    columns = [d[0] for d in cur.description] if cur.description else []
                    data = cur.fetchmany(10001)
                    if len(data) > 10000:
                        data = list(data[:10000])
                    else:
                        data = list(data)
                    return True, data, columns
                self.connection.commit()
                return True, None, None
            except Exception as e:
                return False, str(e), None

    # ---------- write ----------

    def update_cell(self, table_name, column_name, value, rowid):
        with self._lock:
            if not self.connection:
                return False, "Нет подключения"
            if not validate_table_name(table_name) or not validate_column_name(column_name):
                return False, "Неверное имя"
            try:
                cur = self.connection.cursor()
                cur.execute(f'UPDATE "{table_name}" SET "{column_name}" = ? WHERE rowid = ?',
                            (value, rowid))
                self.connection.commit()
                return True, None
            except Exception as e:
                return False, str(e)

    def insert_row(self, table_name, values):
        with self._lock:
            if not self.connection:
                return False, "Нет подключения"
            try:
                cur = self.connection.cursor()
                ph = ", ".join("?" for _ in values)
                cur.execute(f'INSERT INTO "{table_name}" VALUES ({ph})', values)
                self.connection.commit()
                return True, cur.lastrowid
            except Exception as e:
                return False, str(e)

    def delete_row(self, table_name, rowid):
        with self._lock:
            if not self.connection:
                return False, "Нет подключения"
            try:
                cur = self.connection.cursor()
                cur.execute(f'DELETE FROM "{table_name}" WHERE rowid = ?', (rowid,))
                self.connection.commit()
                return True, None
            except Exception as e:
                return False, str(e)

    def add_column(self, table_name, column_name, column_type="TEXT"):
        with self._lock:
            if not validate_table_name(table_name) or not validate_column_name(column_name):
                return False, "Неверное имя"
            try:
                self.connection.execute(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {column_type}')
                self.connection.commit()
                return True, None
            except Exception as e:
                return False, str(e)

    def drop_column(self, table_name, column_name):
        with self._lock:
            if not validate_table_name(table_name) or not validate_column_name(column_name):
                return False, "Неверное имя"
            try:
                self.connection.execute(
                    f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"')
                self.connection.commit()
                return True, None
            except Exception as e:
                return False, str(e)

    def create_table(self, table_name, columns):
        with self._lock:
            if not validate_table_name(table_name):
                return False, "Неверное имя таблицы"
            try:
                parts, pks = [], []
                for col in columns:
                    if not validate_column_name(col["name"]):
                        return False, f"Неверное имя колонки: {col['name']}"
                    d = f'"{col["name"]}" {col["type"]}'
                    if col.get("pk"):
                        pks.append(f'"{col["name"]}"')
                    if col.get("notnull") and not col.get("pk"):
                        d += " NOT NULL"
                    if col.get("default"):
                        d += f" DEFAULT '{col['default']}'"
                    parts.append(d)
                if pks:
                    parts.append(f'PRIMARY KEY ({", ".join(pks)})')
                self.connection.execute(
                    f'CREATE TABLE "{table_name}" (\n' + ",\n".join(parts) + "\n);")
                self.connection.commit()
                return True, None
            except Exception as e:
                return False, str(e)

    def backup_database(self):
        with self._lock:
            if not self.current_db:
                return False, "Нет открытой БД"
            try:
                dst = self.current_db + f".backup_{datetime.now():%Y%m%d_%H%M%S}"
                shutil.copy2(self.current_db, dst)
                return True, f"Резервная копия: {os.path.basename(dst)}"
            except Exception as e:
                return False, f"Ошибка бэкапа: {e}"

    def optimize_database(self):
        with self._lock:
            if not self.connection:
                return False, "Нет подключения"
            try:
                self.connection.execute("VACUUM")
                return True, "БД оптимизирована"
            except Exception as e:
                return False, f"Ошибка оптимизации: {e}"