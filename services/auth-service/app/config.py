from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict
from datetime import timedelta
from pydantic import AnyHttpUrl, validator, PostgresDsn

class Settings(BaseSettings):
    # FastAPI settings
    API_V1_STR: str = "/auth/api/v1"
    APP_TITLE: str = "Bomberman Auth Service"
    HOST: str = "0.0.0.0"
    PORT: int = 5003
    DEBUG: bool = True
    RELOAD: bool = True
    SWAGGER_URL: str = "/auth/api/docs"
    
    # CORS settings
    CORS_ORIGINS: list[str] = ["*"]
    CORS_CREDENTIALS: bool = True
    CORS_METHODS: list[str] = ["*"]
    CORS_HEADERS: list[str] = ["*"]
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 1
    REDIS_PASSWORD: str | None = None
    
    # PostgreSQL settings
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str = "auth_service"
    POSTGRES_USER: str = "bomberman"
    POSTGRES_PASSWORD: str = "bomberman"
    DATABASE_URI: Optional[str] = None
    ASYNC_DATABASE_URI: Optional[str] = None
    
    # JWT settings
    SECRET_KEY: str = "your_secret_key_here"  # В реальном приложении нужно заменить на секретный ключ
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 3000
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OAuth2 settings
    OAUTH2_PROVIDERS: dict = {
        "google": {
            "client_id": "",
            "client_secret": "",
            "authorize_endpoint": "https://accounts.google.com/o/oauth2/auth",
            "token_endpoint": "https://oauth2.googleapis.com/token",
            "userinfo_endpoint": "https://www.googleapis.com/oauth2/v3/userinfo",
            "scope": "openid email profile"
        }
    }
    
    # Frontend settings
    TEMPLATES_DIR: str = "app/templates"
    
    # Roles
    ROLES: list[str] = ["user", "admin", "moderator", "developer"]
    
    # Logging settings
    LOG_LEVEL: str = "DEBUG"
    LOG_FORMAT: str = "json"
    TRACE_CALLER: bool = True

    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        url = f'postgresql://{values.get("POSTGRES_USER")}:{values.get("POSTGRES_PASSWORD")}@{values.get("POSTGRES_HOST")}:{values.get("POSTGRES_PORT")}/{values.get("POSTGRES_DB")}'
        return url

    @validator("ASYNC_DATABASE_URI", pre=True)
    def async_assemble_db_connection(cls, v: Optional[str], values: dict[str, any]) -> any:
        if isinstance(v, str):
            return v
        url = f'postgresql+asyncpg://{values.get("POSTGRES_USER")}:{values.get("POSTGRES_PASSWORD")}@{values.get("POSTGRES_HOST")}:{values.get("POSTGRES_PORT")}/{values.get("POSTGRES_DB")}'
        return url

    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings() 