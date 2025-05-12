import logging
import logging.config
import sys
import time
import os
import socket
import uuid
from pythonjsonlogger import jsonlogger

from .config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        # Основные поля
        log_record["service"] = "game-service"
        log_record["service_type"] = "backend"
        log_record["level"] = record.levelname
        log_record["logger"] = record.name
        log_record["message"] = record.getMessage()
        
        # Дополнительный контекст
        log_record["host"] = socket.gethostname()
        log_record["pid"] = os.getpid()
        log_record["thread_id"] = record.thread
        log_record["thread_name"] = record.threadName
        
        # # Добавляем уникальный идентификатор для каждого лога
        # log_record["log_id"] = str(uuid.uuid4())
        #
        # Добавляем меток времени в секундах с начала эпохи
        log_record["timestamp_epoch"] = int(time.time())
        
        # Если есть исключение, добавляем его информацию
        if record.exc_info:
            log_record["exception"] = self.formatException(record.exc_info)

def configure_logging():
    """Настройка JSON логирования"""
    log_level = getattr(logging, settings.LOG_LEVEL)
    log_handler = logging.StreamHandler(sys.stdout)
    
    # Используем JSON или обычный формат логирования в зависимости от настроек
    if settings.LOG_FORMAT.lower() == "json":
        formatter = CustomJsonFormatter()
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