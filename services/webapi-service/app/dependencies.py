from fastapi import Depends
from typing import AsyncGenerator
import logging

from .services.game_cache import GameInstanceCache
from .services.game_service import GameService
from .services.nats_service import NatsService
from .repositories.redis_repository import RedisRepository
# from .services.socketio_service import SocketIOService

logger = logging.getLogger(__name__)

# Singleton instances
try:
    logger.debug("Initializing singleton instances")
    redis_repository = RedisRepository()
    nats_service = NatsService()
    game_service = GameService(nats_service)
    game_cache = GameInstanceCache(redis_repository=redis_repository)
    logger.info("Singleton instances initialized successfully")
except Exception as e:
    logger.critical(f"Failed to initialize dependency services: {e}", exc_info=True)
    raise

async def get_redis_repository() -> AsyncGenerator[RedisRepository, None]:
    """
    Get Redis repository instance
    """
    try:
        logger.debug("Providing Redis repository dependency")
        yield redis_repository
    except Exception as e:
        logger.error(f"Error providing Redis repository dependency: {e}", exc_info=True)
        raise

async def get_nats_service() -> AsyncGenerator[NatsService, None]:
    """
    Get NATS service instance
    """
    try:
        logger.debug("Providing NATS service dependency")
        yield nats_service
    except Exception as e:
        logger.error(f"Error providing NATS service dependency: {e}", exc_info=True)
        raise

async def get_game_service() -> AsyncGenerator[GameService, None]:
    """
    Get game service instance
    """
    try:
        logger.debug("Providing game service dependency")
        yield game_service
    except Exception as e:
        logger.error(f"Error providing game service dependency: {e}", exc_info=True)
        raise

async def get_game_cache() -> AsyncGenerator[GameInstanceCache, None]:
    """
    Get game cache instance
    """
    try:
        logger.debug("Providing game cache dependency")
        yield game_cache
    except Exception as e:
        logger.error(f"Error providing game cache dependency: {e}", exc_info=True)
        raise