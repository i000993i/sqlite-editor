from pathlib import Path
import os
import sys

APP_NAME = "SQLiteViewer"


def app_dir() -> Path:
    """Каталог, рядом с которым лежит исполняемый файл/скрипт."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


def user_data_dir() -> Path:
    """Пользовательский каталог для логов/истории (кроссплатформенно)."""
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", Path.home()))
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    p = base / APP_NAME
    p.mkdir(parents=True, exist_ok=True)
    return p


def logs_dir() -> Path:
    p = user_data_dir() / "logs"
    p.mkdir(parents=True, exist_ok=True)
    return p


def icons_dir() -> Path:
    return app_dir() / "icons"


def history_file() -> Path:
    return user_data_dir() / "query_history.json"