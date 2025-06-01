from typing import Optional

from pydantic import field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI settings
    API_V1_STR: str = "/games/api/v1"
    APP_TITLE: str = "Bomberman Game Service"
    HOST: str = "0.0.0.0"
    PORT: int = 5002
    DEBUG: bool = True
    RELOAD: bool = True
    SWAGGER_URL: str = "/games/docs"
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "game_service"
    POSTGRES_USER: str = "bomberman"
    POSTGRES_PASSWORD: str = "bomberman"
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    
    # Game engine settings (не настраиваемые пользователями)
    GAME_UPDATE_FPS: float = 30.0
    GAME_OVER_TIMEOUT: float = 5.0  # секунды
    
    # Game settings
    CELL_SIZE: int = 40
    MAP_WIDTH: int = 15
    MAP_HEIGHT: int = 13
    MAX_PLAYERS: int = 4
    
    # NATS settings
    NATS_URL: str = "nats://localhost:4222"

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    TRACE_CALLER: bool = True

    @computed_field
    @property
    def DATABASE_URI(self) -> str:
        return f'postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    @computed_field
    @property
    def ASYNC_DATABASE_URI(self) -> str:
        return f'postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}'

    @computed_field
    @property
    def REDIS_URI(self) -> str:
        """Получить URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings() 