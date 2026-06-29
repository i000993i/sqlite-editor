import pandas as pd
import json
import os
from functions.logger import utils_logger
from functions.utils import validate_table_name

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
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        
        try:
            first_chunk = True
            safe_table = f'"{table_name}"'
            
            for chunk in pd.read_sql_query(f"SELECT * FROM {safe_table}", 
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
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        
        try:
            safe_table = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe_table}", connection)
            df.to_json(file_path, orient='records', indent=2, force_ascii=False)
            
            return True, f"Таблица экспортирована в {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"
    
    def export_excel(self, table_name, file_path, connection):
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        
        try:
            safe_table = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe_table} LIMIT 1000000", connection)
            
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name=table_name, index=False)
            
            if len(df) == 1000000:
                return True, f"Таблица экспортирована (1,000,000 записей, макс. для Excel)"
            else:
                return True, f"Таблица экспортирована в {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта: {str(e)}"
    
    _font_registered = False

    def _register_unicode_font(self):
        if ImportExportManager._font_registered:
            return 'UnicodeFont'
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        
        if os.name == 'nt':
            windir = os.environ.get('WINDIR', 'C:\\Windows')
            candidates = [
                os.path.join(windir, 'Fonts', 'seguiemj.ttf'),
                os.path.join(windir, 'Fonts', 'segoeui.ttf'),
                os.path.join(windir, 'Fonts', 'segoeuib.ttf'),
                os.path.join(windir, 'Fonts', 'arial.ttf'),
                os.path.join(windir, 'Fonts', 'arialbd.ttf'),
            ]
        else:
            candidates = [
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf',
                '/usr/share/fonts/TTF/DejaVuSans.ttf',
            ]
        
        for path in candidates:
            try:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont('UnicodeFont', path))
                    bold_path = path.replace('.ttf', 'b.ttf') if path.endswith('.ttf') else None
                    if bold_path and os.path.exists(bold_path):
                        pdfmetrics.registerFont(TTFont('UnicodeFont-Bold', bold_path))
                    else:
                        pdfmetrics.registerFont(TTFont('UnicodeFont-Bold', path))
                    ImportExportManager._font_registered = True
                    return 'UnicodeFont'
            except Exception:
                continue
        return 'Helvetica'
    
    def export_pdf(self, table_name, file_path, connection, title=None):
        """Экспорт таблицы в PDF"""
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import inch
            
            font_name = self._register_unicode_font()
            
            safe_table = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe_table} LIMIT 10000", connection)
            
            if df.empty:
                return False, "Таблица пуста"
            
            if len(df) > 10000:
                df = df.head(10000)
                truncated = True
            else:
                truncated = False
            
            doc = SimpleDocTemplate(
                file_path,
                pagesize=landscape(A4),
                rightMargin=30,
                leftMargin=30,
                topMargin=30,
                bottomMargin=30
            )
            
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName=font_name,
                fontSize=16,
                textColor=colors.HexColor('#333333'),
                spaceAfter=20
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontName=font_name,
                fontSize=10,
            )
            
            elements = []
            
            table_title = title or f"Таблица: {table_name}"
            elements.append(Paragraph(table_title, title_style))
            elements.append(Spacer(1, 10))
            
            info_text = f"Всего записей: {len(df)}"
            if truncated:
                info_text += " (показаны первые 10000)"
            elements.append(Paragraph(info_text, normal_style))
            elements.append(Spacer(1, 20))
            
            max_cols = 8
            if len(df.columns) > max_cols:
                df = df.iloc[:, :max_cols]
            
            data = [list(df.columns)]
            for _, row in df.iterrows():
                data.append([str(val)[:100] for val in row])
            
            table = Table(data)
            
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#404040')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), font_name),
                ('FONTNAME', (0, 1), (-1, -1), font_name),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cccccc')),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ])
            
            table.setStyle(style)
            elements.append(table)
            
            doc.build(elements)
            
            result_msg = f"Таблица экспортирована в {os.path.basename(file_path)}"
            if truncated:
                result_msg += " (10000 записей, лимит PDF)"
            
            return True, result_msg
        except Exception as e:
            return False, f"Ошибка экспорта PDF: {str(e)}"