import logging
import logging.config
import sys
from pythonjsonlogger import jsonlogger

from .config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record["service"] = "game-service"  # Меняем имя сервиса
        log_record["level"] = record.levelname
        log_record["logger"] = record.name

def configure_logging():
    """Настройка JSON логирования"""
    log_level = getattr(logging, settings.LOG_LEVEL)
    log_handler = logging.StreamHandler(sys.stdout)
    
    # Используем JSON или обычный формат логирования в зависимости от настроек
    if settings.LOG_FORMAT.lower() == "json":
        formatter = CustomJsonFormatter(
            "%(timestamp)s %(service)s %(level)s %(name)s %(message)s",
            timestamp=True
        )
    else:
        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | game-service | %(name)s | %(message)s"
        )
    
    log_handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=log_level,
        handlers=[log_handler],
    )
    
    # Отключаем лишние логи от библиотек
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Настройка корневого логгера
    root_logger = logging.getLogger()
    root_logger.handlers = [log_handler] 