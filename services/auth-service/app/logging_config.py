import logging
import json
import sys
import traceback
from typing import Callable, Any
from datetime import datetime
from logging import LogRecord
from pythonjsonlogger import jsonlogger

from .config import settings

class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: dict, record: LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Добавляем дополнительные поля в лог
        log_record["timestamp"] = datetime.utcnow().isoformat()
        log_record["level"] = record.levelname
        log_record["service"] = "auth-service"
        
        # Добавляем трейс вызова если включено
        if settings.TRACE_CALLER and record.levelno >= logging.WARNING:
            log_record["caller"] = f"{record.pathname}:{record.lineno}"
        
        # Добавляем trace_id если есть
        trace_id = getattr(record, "trace_id", None)
        if trace_id:
            log_record["trace_id"] = trace_id

        # Добавляем данные исключения если есть
        if record.exc_info:
            log_record["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }

class TraceIDFilter(logging.Filter):
    """Фильтр для добавления trace_id в записи логов."""
    
    def __init__(self, name: str = "", trace_getter: Callable[[], str] = None):
        super().__init__(name)
        self.trace_getter = trace_getter or (lambda: "")
    
    def filter(self, record: LogRecord) -> bool:
        record.trace_id = self.trace_getter()
        return True

def configure_logging() -> None:
    """Настраивает логирование для приложения."""
    root_logger = logging.getLogger()
    
    # Удаляем существующие обработчики
    while root_logger.handlers:
        root_logger.removeHandler(root_logger.handlers[0])
    
    # Устанавливаем уровень логирования
    root_logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))
    
    # Создаем консольный обработчик
    console_handler = logging.StreamHandler(sys.stdout)
    
    if settings.LOG_FORMAT.lower() == "json":
        # Создаем JSON форматер
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Стандартный текстовый форматтер
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    # Устанавливаем форматтер для обработчика
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчик к корневому логгеру
    root_logger.addHandler(console_handler)
    
    # Устанавливаем фильтр для добавления trace_id
    # trace_filter = TraceIDFilter(trace_getter=get_trace_id)
    # root_logger.addFilter(trace_filter)
    
    # Настраиваем стандартные библиотеки
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING) 