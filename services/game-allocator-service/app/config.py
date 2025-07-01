from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI settings
    SERVICE_NAME: str = "game-allocator-service"
    APP_TITLE: str = "Bomberman Game Allocator Service"

    GAME_CACHE_TTL: int = 60

    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None

    # NATS settings
    NATS_URL: str = "nats://localhost:4222"
    PROMETHEUS_URL: str = "http://prometheus:9090"
    CONSUL_HOST: str = "consul"

    # Logging settings
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "text" #json
    TRACE_CALLER: bool = True

    @computed_field
    @property
    def REDIS_URI(self) -> str:
        """Получить URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8', extra='ignore')

settings = Settings() 