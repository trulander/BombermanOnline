from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI settings
    API_V1_STR: str = "/api/v1"
    APP_TITLE: str = "Bomberman Online"
    HOST: str = "0.0.0.0"
    PORT: int = 5000
    DEBUG: bool = True
    RELOAD: bool = True
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    
    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "bomberman"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    
    # Game settings
    CELL_SIZE: int = 40
    MAP_WIDTH: int = 15
    MAP_HEIGHT: int = 13
    MAX_PLAYERS: int = 4
    GAME_UPDATE_RATE: float = 0.023  # ~30 FPS
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()