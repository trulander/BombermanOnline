from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # FastAPI settings
    SERVICE_NAME: str = "webapi-service"
    API_V1_STR: str = "/webapi/api/v1"
    APP_TITLE: str = "Bomberman WebAPI Service"
    HOST: str = "0.0.0.0"
    PORT: int = 5001
    DEBUG: bool = True
    RELOAD: bool = True
    SWAGGER_URL: str = "/webapi/docs"
    HOSTNAME: str = "localhost"

    CONSUL_HOST: str = "localhost"

    #TODO доработать логику получения хоста через консул динамически
    GAME_SERVICE_HOSTNAME: str = "localhost"
    
    # CORS settings
    CORS_ORIGINS: str = "*"
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str | None = None
    

    # NATS settings
    NATS_URL: str = "nats://localhost:4222"
    

    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "text"#json
    TRACE_CALLER: bool = True

    @computed_field
    @property
    def REDIS_URI(self) -> str:
        """Получить URL для подключения к Redis"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings() 