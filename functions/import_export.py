import pandas as pd
import json
import os

class ImportExportManager:
    def __init__(self):
        self.chunk_size = 10000
    
    def import_csv(self, file_path, connection):
        try:
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            first_chunk = True
            
            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                if first_chunk:
                    chunk.to_sql(table_name, connection, if_exists='replace', index=False)
                    first_chunk = False
                else:
                    chunk.to_sql(table_name, connection, if_exists='append', index=False)
            
            return True, f"Данные импортированы в таблицу {table_name}"
        except Exception as e:
            return False, f"Ошибка импорта: {str(e)}"
    
    def import_json(self, file_path, connection):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            df = pd.DataFrame(data)
            table_name = os.path.splitext(os.path.basename(file_path))[0]
            
            df.to_sql(table_name, connection, if_exists='replace', index=False)
            
            return True, f"Данные импортированы в таблицу {table_name}"
        except Exception as e:
            return False, f"Ошибка импорта: {str(e)}"
    
    def export_csv(self, table_name, file_path, connection):
        try:
            first_chunk = True
            
            for chunk in pd.read_sql_query(f"SELECT * FROM {table_name}", 
                                          connection, chunksize=self.chunk_size):
                if first_chunk:
                    chunk.to_csv(file_path, index=False, encoding='utf-8')
                    first_chunk = False
                else:
                    chunk.to_csv(file_path, mode='a', header=False, index=False, encoding='utf-8')
            
            return True, f"Таблица экспортирована в {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"
    
    def export_json(self, table_name, file_path, connection):
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", connection)
            df.to_json(file_path, orient='records', indent=2, force_ascii=False)
            
            return True, f"Таблица экспортирована в {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"
    
    def export_excel(self, table_name, file_path, connection):
        try:
            df = pd.read_sql_query(f"SELECT * FROM {table_name} LIMIT 1000000", connection)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)
            
            if len(df) == 1000000:
                return True, f"Таблица экспортирована (1,000,000 записей, макс. для Excel)"
            else:
                return True, f"Таблица экспортирована в {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"