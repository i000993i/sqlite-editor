import logging
import sys
from functions.paths import logs_dir

LOG_LEVEL = logging.INFO
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logger(name: str, log_file: str = None, level: int = LOG_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # На Windows консоль в GUI-сборке отсутствует — не падаем
    if sys.stderr is not None:
        ch = logging.StreamHandler(sys.stderr)
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    if log_file:
        path = logs_dir() / log_file
        fh = logging.FileHandler(path, encoding="utf-8")
        fh.setLevel(level)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    return logger


db_logger     = setup_logger("database", "database.log")
models_logger = setup_logger("models",   "models.log")
main_logger   = setup_logger("main",     "app.log")
utils_logger  = setup_logger("utils",    "utils.log")