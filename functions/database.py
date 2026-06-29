import sqlite3
import os
from datetime import datetime
import shutil
from typing import Callable
from functions.logger import db_logger
from functions.utils import validate_table_name, validate_column_name, validate_order_by

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.current_db = None
        self.query_history = []

    def connect(self, db_path):
        try:
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.current_db = db_path
            db_logger.info(f"Подключение к БД: {db_path}")
            return True
        except Exception as e:
            db_logger.error(f"Ошибка подключения {db_path}: {e}")
            return False

    def create_database(self, db_path):
        try:
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.current_db = db_path
            db_logger.info(f"БД создана: {db_path}")
            return True
        except Exception as e:
            db_logger.error(f"Ошибка создания {db_path}: {e}")
            return False

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            self.current_db = None

    def get_tables(self):
        if not self.connection:
            return []
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        result = []
        for table in tables:
            table_name = table[0]
            if validate_table_name(table_name):
                cursor.execute(f"SELECT COUNT(*) FROM \"{table_name}\"")
                count = cursor.fetchone()[0]
                result.append((table_name, count))
        return result

    def get_table_names(self):
        if not self.connection:
            return []
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall() if validate_table_name(table[0])]

    def execute_query(self, query):
        if not self.connection:
            return False, "Нет подключения к БД", None
        try:
            self.query_history.append({
                'query': query,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            cursor = self.connection.cursor()
            cursor.execute(query)
            if query.upper().strip().startswith("SELECT"):
                columns = [description[0] for description in cursor.description] if cursor.description else []
                data = cursor.fetchmany(10001)
                if len(data) > 10000:
                    data = list(data[:10000])
                else:
                    data = list(data)
                return True, data, columns
            else:
                self.connection.commit()
                return True, None, None
        except Exception as e:
            return False, str(e), None

    def backup_database(self):
        if not self.current_db:
            return False, "Нет открытой базы данных"
        try:
            backup_path = self.current_db + f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(self.current_db, backup_path)
            return True, f"Резервная копия: {os.path.basename(backup_path)}"
        except Exception as e:
            return False, f"Ошибка бэкапа: {str(e)}"

    def optimize_database(self):
        if not self.connection:
            return False, "Нет подключения к БД"
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM;")
            return True, "БД оптимизирована"
        except Exception as e:
            return False, f"Ошибка оптимизации: {str(e)}"

    def get_table_page(self, table_name: str, offset: int = 0, limit: int = 100,
                       order_by: str = None, where_clause: str = None,
                       progress_callback: Callable = None) -> tuple:
        if not self.connection:
            return False, [], [], 0, "Нет подключения к БД"
        if not validate_table_name(table_name):
            return False, [], [], 0, "Неверное имя таблицы"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            if progress_callback:
                progress_callback(10, "Подсчёт строк...")
            cursor.execute(f"SELECT COUNT(*) FROM {safe_table}")
            total_count = cursor.fetchone()[0]
            if progress_callback:
                progress_callback(30, "Загрузка данных...")
            query = f"SELECT rowid, * FROM {safe_table}"
            if where_clause:
                query += f" WHERE {where_clause}"
            if order_by:
                if validate_order_by(order_by):
                    query += f" ORDER BY {order_by}"
                else:
                    db_logger.warning(f"Некорректный ORDER BY: {order_by}, использую ROWID")
                    query += " ORDER BY ROWID"
            else:
                query += " ORDER BY ROWID"
            query += f" LIMIT {int(limit)} OFFSET {int(offset)}"
            if progress_callback:
                progress_callback(50, "Выполнение запроса...")
            cursor.execute(query)
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description] if cursor.description else []
            if progress_callback:
                progress_callback(100, "Готово")
            db_logger.debug(f"Страница {offset}-{offset+limit} из {total_count} для {table_name}")
            return True, data, columns, total_count, None
        except Exception as e:
            error_msg = str(e)
            db_logger.error(f"Ошибка загрузки страницы {table_name}: {error_msg}")
            return False, [], [], 0, error_msg

    def get_table_schema(self, table_name: str) -> dict:
        if not self.connection:
            return None
        if not validate_table_name(table_name):
            return None
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            cursor.execute(f"PRAGMA table_info({safe_table})")
            columns_info = cursor.fetchall()
            columns = []
            primary_key = None
            has_rowid = True
            for col in columns_info:
                col_info = {
                    'name': col[1],
                    'type': col[2] or 'TEXT',
                    'notnull': bool(col[3]),
                    'default': col[4],
                    'primary_key': bool(col[5])
                }
                columns.append(col_info)
                if col[5]:
                    primary_key = col[1]
            cursor.execute(f"SELECT ROWID FROM {safe_table} LIMIT 1")
            has_rowid = cursor.fetchone() is not None
            return {
                'columns': columns,
                'primary_key': primary_key,
                'has_rowid': has_rowid
            }
        except Exception as e:
            db_logger.error(f"Ошибка схемы {table_name}: {e}")
            return None

    def search_table(self, table_name: str, search_text: str, limit: int = 100,
                     progress_callback: Callable = None) -> tuple:
        if not self.connection:
            return False, [], [], 0, "Нет подключения к БД"
        if not validate_table_name(table_name):
            return False, [], [], 0, "Неверное имя таблицы"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            schema = self.get_table_schema(table_name)
            if not schema:
                return False, [], [], 0, "Не удалось получить схему"
            text_columns = [col['name'] for col in schema['columns']
                          if col['type'] in ('TEXT', 'VARCHAR', 'CHAR', 'CLOB')]
            if not text_columns:
                text_columns = [col['name'] for col in schema['columns']]
            search_pattern = f"%{search_text}%"
            where_conditions = [f'"{col}" LIKE ?' for col in text_columns]
            where_clause = " OR ".join(where_conditions)
            if progress_callback:
                progress_callback(10, "Подсчёт результатов...")
            count_query = f"SELECT COUNT(*) FROM {safe_table} WHERE {where_clause}"
            cursor.execute(count_query, [search_pattern] * len(text_columns))
            total_count = cursor.fetchone()[0]
            if progress_callback:
                progress_callback(40, "Загрузка результатов...")
            data_query = f"SELECT rowid, * FROM {safe_table} WHERE {where_clause} LIMIT ?"
            cursor.execute(data_query, [search_pattern] * len(text_columns) + [int(limit)])
            data = cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            if progress_callback:
                progress_callback(100, "Готово")
            db_logger.info(f"Поиск '{search_text}' в {table_name}: {total_count} результатов")
            return True, data, columns, total_count, None
        except Exception as e:
            error_msg = str(e)
            db_logger.error(f"Ошибка поиска в {table_name}: {error_msg}")
            return False, [], [], 0, error_msg

    def update_cell(self, table_name: str, column_name: str, value, rowid: int) -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        if not validate_column_name(column_name):
            return False, "Неверное имя колонки"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            safe_col = f'"{column_name}"'
            cursor.execute(f"UPDATE {safe_table} SET {safe_col} = ? WHERE rowid = ?", (value, rowid))
            self.connection.commit()
            return True, None
        except Exception as e:
            return False, str(e)

    def insert_row(self, table_name: str, values: list) -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            placeholders = ', '.join('?' for _ in values)
            cursor.execute(f"INSERT INTO {safe_table} VALUES ({placeholders})", values)
            self.connection.commit()
            new_rowid = cursor.lastrowid
            db_logger.info(f"Строка добавлена в {table_name}, rowid={new_rowid}")
            return True, new_rowid
        except Exception as e:
            return False, str(e)

    def delete_row(self, table_name: str, rowid: int) -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            cursor.execute(f"DELETE FROM {safe_table} WHERE rowid = ?", (rowid,))
            self.connection.commit()
            db_logger.info(f"Строка rowid={rowid} удалена из {table_name}")
            return True, None
        except Exception as e:
            return False, str(e)

    def add_column(self, table_name: str, column_name: str, column_type: str = 'TEXT') -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        if not validate_column_name(column_name):
            return False, "Неверное имя колонки"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            safe_col = f'"{column_name}"'
            cursor.execute(f"ALTER TABLE {safe_table} ADD COLUMN {safe_col} {column_type}")
            self.connection.commit()
            db_logger.info(f"Колонка {column_name} добавлена в {table_name}")
            return True, None
        except Exception as e:
            return False, str(e)

    def drop_column(self, table_name: str, column_name: str) -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        if not validate_column_name(column_name):
            return False, "Неверное имя колонки"
        try:
            cursor = self.connection.cursor()
            safe_table = f'"{table_name}"'
            safe_col = f'"{column_name}"'
            cursor.execute(f"ALTER TABLE {safe_table} DROP COLUMN {safe_col}")
            self.connection.commit()
            db_logger.info(f"Колонка {column_name} удалена из {table_name}")
            return True, None
        except Exception as e:
            return False, str(e)

    def create_table(self, table_name: str, columns: list) -> tuple:
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            parts = []
            pk_cols = []
            for col in columns:
                col_name = col["name"]
                if not validate_column_name(col_name):
                    return False, f"Неверное имя колонки: {col_name}"
                col_def = f'  "{col_name}" {col["type"]}'
                if col.get('pk'):
                    pk_cols.append(f'"{col_name}"')
                if col.get('notnull') and not col.get('pk'):
                    col_def += ' NOT NULL'
                if col.get('default'):
                    col_def += f" DEFAULT '{col['default']}'"
                parts.append(col_def)
            if pk_cols:
                parts.append(f'  PRIMARY KEY ({", ".join(pk_cols)})')
            sql = f'CREATE TABLE "{table_name}" (\n' + ',\n'.join(parts) + '\n);'
            cursor = self.connection.cursor()
            cursor.execute(sql)
            self.connection.commit()
            db_logger.info(f"Таблица {table_name} создана")
            return True, None
        except Exception as e:
            return False, str(e)
