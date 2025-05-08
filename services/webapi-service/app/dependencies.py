from fastapi import Depends
from typing import AsyncGenerator

from .services.game_service import GameService
from .services.nats_service import NatsService
from .repositories.redis_repository import RedisRepository
# from .services.socketio_service import SocketIOService

# Singleton instances
redis_repository = RedisRepository()
nats_service = NatsService()
game_service = GameService(nats_service)

async def get_redis_repository() -> AsyncGenerator[RedisRepository, None]:
    """
    Get Redis repository instance
    """
    yield redis_repository

async def get_nats_service() -> AsyncGenerator[NatsService, None]:
    """
    Get NATS service instance
    """
    yield nats_service

async def get_game_service() -> AsyncGenerator[GameService, None]:
    """
    Get game service instance
    """
    yield game_service 