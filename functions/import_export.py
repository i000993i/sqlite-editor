import json
import os

import pandas as pd

from functions.logger import utils_logger
from functions.utils import validate_table_name, safe_table_name


class ImportExportManager:

    def __init__(self):
        self.chunk_size = 10_000
        self._font_registered = False
        self._font_name = "Helvetica"

    # ---------------- import ----------------

    def import_csv(self, file_path: str, connection):
        try:
            table = safe_table_name(os.path.splitext(os.path.basename(file_path))[0])
            first = True
            for chunk in pd.read_csv(file_path, chunksize=self.chunk_size):
                chunk.to_sql(table, connection,
                             if_exists="replace" if first else "append",
                             index=False)
                first = False
            return True, f"Данные импортированы в таблицу {table}"
        except Exception as e:
            return False, f"Ошибка импорта CSV: {e}"

    def import_json(self, file_path: str, connection):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
            table = safe_table_name(os.path.splitext(os.path.basename(file_path))[0])
            df.to_sql(table, connection, if_exists="replace", index=False)
            return True, f"Данные импортированы в таблицу {table}"
        except Exception as e:
            return False, f"Ошибка импорта JSON: {e}"

    # ---------------- export ----------------

    def export_csv(self, table_name: str, file_path: str, connection):
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            first = True
            safe = f'"{table_name}"'
            for chunk in pd.read_sql_query(f"SELECT * FROM {safe}", connection,
                                           chunksize=self.chunk_size):
                chunk.to_csv(file_path,
                             mode="w" if first else "a",
                             header=first,
                             index=False,
                             encoding="utf-8-sig")  # BOM для Excel
                first = False
            return True, f"Экспорт: {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта CSV: {e}"

    def export_json(self, table_name: str, file_path: str, connection):
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            safe = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe}", connection)
            df.to_json(file_path, orient="records", indent=2, force_ascii=False)
            return True, f"Экспорт: {os.path.basename(file_path)}"
        except Exception as e:
            return False, f"Ошибка экспорта JSON: {e}"

    def export_excel(self, table_name: str, file_path: str, connection):
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            safe = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe} LIMIT 1000000", connection)
            with pd.ExcelWriter(file_path, engine="openpyxl") as writer:
                df.to_excel(writer, sheet_name=table_name[:31], index=False)
            msg = f"Экспорт: {os.path.basename(file_path)}"
            if len(df) == 1_000_000:
                msg += " (максимум 1M для Excel)"
            return True, msg
        except Exception as e:
            return False, f"Ошибка экспорта Excel: {e}"

    # ---------------- PDF ----------------

    def _register_font(self) -> str:
        if self._font_registered:
            return self._font_name
        try:
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont

            if os.name == "nt":
                windir = os.environ.get("WINDIR", r"C:\Windows")
                cands = [
                    os.path.join(windir, "Fonts", "segoeui.ttf"),
                    os.path.join(windir, "Fonts", "arial.ttf"),
                ]
            else:
                cands = [
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
                    "/usr/share/fonts/TTF/DejaVuSans.ttf",
                    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
                ]

            for path in cands:
                if os.path.exists(path):
                    pdfmetrics.registerFont(TTFont("UniFont", path))
                    self._font_name = "UniFont"
                    self._font_registered = True
                    return "UniFont"
        except Exception as e:
            utils_logger.error(f"PDF font: {e}")
        self._font_name = "Helvetica"
        self._font_registered = True
        return "Helvetica"

    def export_pdf(self, table_name: str, file_path: str, connection,
                   title: str | None = None):
        if not validate_table_name(table_name):
            return False, "Неверное имя таблицы"
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4, landscape
            from reportlab.platypus import (
                SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer)
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

            font = self._register_font()
            safe = f'"{table_name}"'
            df = pd.read_sql_query(f"SELECT * FROM {safe} LIMIT 10000", connection)
            if df.empty:
                return False, "Таблица пуста"

            truncated = len(df) > 10_000
            if truncated:
                df = df.head(10_000)

            doc = SimpleDocTemplate(
                file_path, pagesize=landscape(A4),
                rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)

            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                "CT", parent=styles["Heading1"], fontName=font, fontSize=16,
                textColor=colors.HexColor("#333333"), spaceAfter=20)
            normal = ParagraphStyle(
                "CN", parent=styles["Normal"], fontName=font, fontSize=10)

            elements = [Paragraph(title or f"Таблица: {table_name}", title_style),
                        Spacer(1, 10)]
            info = f"Всего записей: {len(df)}"
            if truncated:
                info += " (показаны первые 10000)"
            elements.append(Paragraph(info, normal))
            elements.append(Spacer(1, 20))

            if len(df.columns) > 8:
                df = df.iloc[:, :8]

            data = [list(df.columns)]
            for _, row in df.iterrows():
                data.append([str(v)[:100] for v in row])

            table = Table(data)
            table.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#404040")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("FONTNAME", (0, 0), (-1, -1), font),
                ("FONTSIZE", (0, 0), (-1, 0), 10),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                ("BACKGROUND", (0, 1), (-1, -1), colors.white),
                ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#cccccc")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                 [colors.white, colors.HexColor("#f5f5f5")]),
            ]))
            elements.append(table)
            doc.build(elements)

            msg = f"Экспорт: {os.path.basename(file_path)}"
            if truncated:
                msg += " (лимит 10 000)"
            return True, msg
        except Exception as e:
            return False, f"Ошибка экспорта PDF: {e}"