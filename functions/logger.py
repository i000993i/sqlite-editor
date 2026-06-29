import logging
import sys
from pathlib import Path

# Конфигурация логирования
LOG_LEVEL = logging.INFO
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def setup_logger(name: str, log_file: str = None, level: int = LOG_LEVEL) -> logging.Logger:
    """
    Создание и настройка логгера
    
    Args:
        name: Имя логгера
        log_file: Путь к файлу логов (опционально)
        level: Уровень логирования
        
    Returns:
        Настроенный логгер
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Избегаем дублирования обработчиков
    if logger.handlers:
        return logger
    
    # Форматтер
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Обработчик для файла (если указан)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Создаём логгеры для модулей
db_logger = setup_logger('database', 'logs/database.log')
models_logger = setup_logger('models', 'logs/models.log')
main_logger = setup_logger('main', 'logs/app.log')
utils_logger = setup_logger('utils', 'logs/utils.log')
