import socket
from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    SERVICE_NAME: str = "ai-service"
    APP_TITLE: str = "Bomberman AI Service"
    API_V1_STR: str = "/ai-service/api/v1"
    SWAGGER_URL: str = "/ai-service/docs"

    HOST: str = "0.0.0.0"
    PORT: int = 5004
    DEBUG: bool = True
    RELOAD: bool = True

    HOSTNAME: str = socket.gethostname()

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

    #observation settings
    GRID_CHANNELS: int = 5
    WINDOW_SIZE: int = 15
    STATS_SIZE: int = 7

    # Training settings
    CHECKPOINT_FREQ: int = 10000
    ENABLE_EVALUATION: bool = True
    EVAL_FREQ: int = 5000
    N_EVAL_EPISODES: int = 5
    MAX_NO_IMPROVEMENT_EVALS: int = 10
    MIN_EVALS: int = 5


    # NATS settings for game-allocator-service
    NATS_URL: str = "nats://localhost:4222"
    GAME_ALLOCATOR_SERVICE_NATS_SUBJECT: str = "game.instances.request"

settings: Settings = Settings()