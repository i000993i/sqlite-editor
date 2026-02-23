import sqlite3
import os
from datetime import datetime
import shutil

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.current_db = None
        self.query_history = []
    
    def connect(self, db_path):
        try:
            self.connection = sqlite3.connect(db_path)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.current_db = db_path
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def create_database(self, db_path):
        try:
            self.connection = sqlite3.connect(db_path)
            self.connection.execute("PRAGMA journal_mode=WAL")
            self.connection.execute("PRAGMA foreign_keys=ON")
            self.current_db = db_path
            return True
        except Exception as e:
            print(f"Error creating database: {e}")
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
            cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
            count = cursor.fetchone()[0]
            result.append((table_name, count))
        
        return result
    
    def get_table_names(self):
        if not self.connection:
            return []
        
        cursor = self.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        return [table[0] for table in cursor.fetchall()]
    
    def execute_query(self, query):
        if not self.connection:
            return False, "Нет подключения к БД", None
        
        try:
            # Сохраняем в историю
            self.query_history.append({
                'query': query,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            
            cursor = self.connection.cursor()
            cursor.execute(query)
            
            if query.upper().strip().startswith("SELECT"):
                data = cursor.fetchall()
                columns = [description[0] for description in cursor.description] if cursor.description else []
                
                # Ограничиваем для производительности
                if len(data) > 10000:
                    data = data[:10000]
                
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
            return True, f"Резервная копия создана: {os.path.basename(backup_path)}"
        except Exception as e:
            return False, f"Ошибка создания резервной копии: {str(e)}"
    
    def optimize_database(self):
        if not self.connection:
            return False, "Нет подключения к БД"
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("VACUUM;")
            return True, "База данных оптимизирована"
        except Exception as e:
            return False, f"Ошибка оптимизации: {str(e)}"