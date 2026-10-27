import os
import re
import sys
from pathlib import Path
from functions.logger import utils_logger

TABLE_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")
COLUMN_NAME_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def validate_table_name(name):
    return bool(name) and isinstance(name, str) and bool(TABLE_NAME_PATTERN.match(name))


def validate_column_name(name):
    return bool(name) and isinstance(name, str) and bool(COLUMN_NAME_PATTERN.match(name))


def validate_order_by(order_by):
    if not order_by or not isinstance(order_by, str):
        return False
    parts = order_by.strip().split()
    if not parts or len(parts) > 2:
        return False
    if not validate_column_name(parts[0].strip('"')):
        return False
    return len(parts) == 1 or parts[1].upper() in ("ASC", "DESC")


def format_size(size):
    for unit in ("Б", "КБ", "МБ", "ГБ"):
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} ТБ"


def truncate_string(text, max_length=100):
    return text if len(text) <= max_length else text[: max_length - 3] + "..."


def safe_table_name(name):
    return re.sub(r"[^a-zA-Z0-9_]", "_", name)


# ---- cross-platform ----

def is_windows() -> bool:
    return os.name == "nt"


def monospace_font_family() -> str:
    """Возвращает моноширинный шрифт, доступный в системе."""
    if is_windows():
        return "Consolas"
    # Linux / Zorin OS
    for family in ("JetBrains Mono", "DejaVu Sans Mono", "Liberation Mono", "monospace"):
        # QFontDatabase требует Qt — проверку сделаем в вызывающем коде
        # Здесь просто отдаём предпочтительный
        return family if family == "monospace" else family
    return "monospace"


def open_in_explorer(path: str) -> None:
    """Открыть папку с файлом в системном файловом менеджере."""
    p = Path(path)
    if not p.exists():
        return
    if is_windows():
        os.startfile(str(p))  # noqa: S606
    else:
        import subprocess
        subprocess.Popen(["xdg-open", str(p)])


def project_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent