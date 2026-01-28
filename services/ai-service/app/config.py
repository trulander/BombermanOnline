import logging
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Конфигурация логирования
def configure_logging(log_level: str, log_format: str, trace_caller: bool) -> None:
    log_level = log_level.upper()
    
    # Configure json logger
    if log_format == "text":
        from pythonjsonlogger import jsonlogger
        
        formatter = jsonlogger.JsonFormatter()

            
        handler = logging.StreamHandler()
        handler.setFormatter(formatter)
        
        # Clear existing handlers to prevent duplicate logs
        logging.root.handlers = []
        logging.root.addHandler(handler)
        logging.root.setLevel(log_level)
    else:
        logging.basicConfig(level=log_level, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    logging.getLogger("uvicorn").propagate = False
    logging.getLogger("uvicorn.access").propagate = False
    logging.getLogger("uvicorn.error").propagate = False
    logging.getLogger("fastapi").propagate = False
    logging.getLogger("httpx").propagate = False
    logging.getLogger("httpcore").propagate = False

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    SERVICE_NAME: str = "ai-service"
    APP_TITLE: str = "Bomberman AI Service"

    HOST: str = "0.0.0.0"
    PORT: int = 5004
    DEBUG: bool = True
    RELOAD: bool = True

    HOSTNAME: str = "localhost"

    CONSUL_HOST: str = "localhost"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # gRPC settings
    GRPC_HOST: str = "0.0.0.0"
    GRPC_PORT: int = 50051

    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    TRACE_CALLER: bool = True

    MODELS_PATH: Path = Path("./app/ai_models")
    LOGS_PATH: Path = Path("./app/ai_logs")

    # NATS settings for game-allocator-service
    NATS_URL: str = "nats://localhost:4222"
    GAME_ALLOCATOR_SERVICE_NATS_SUBJECT: str = "game.instances.request"

@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    configure_logging(settings.LOG_LEVEL, settings.LOG_FORMAT, settings.TRACE_CALLER)
    return settings

settings: Settings = get_settings()