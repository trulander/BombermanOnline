import json
import logging
from typing import Any

import redis.asyncio as redis
from ..config import settings

logger = logging.getLogger(__name__)

class RedisRepository:
    """Repository for Redis"""
    
    def __init__(self) -> None:
        """Initialize Redis repository"""
        self._redis: redis.Redis | None = None
        logger.info(f"Redis repository initialized with host={settings.REDIS_HOST}, port={settings.REDIS_PORT}, db={settings.REDIS_DB}")
    
    async def get_redis(self) -> redis.Redis:
        """Get Redis connection with caching"""
        try:
            if self._redis is None or self._redis.connection_pool.connection_class is None:
                logger.info(f"Connecting to Redis server at {settings.REDIS_HOST}:{settings.REDIS_PORT}")
                self._redis = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD,
                    decode_responses=True
                )
                # Test connection
                await self._redis.ping()
                logger.info(f"Connected to Redis: {settings.REDIS_HOST}:{settings.REDIS_PORT}")
            return self._redis
        except Exception as e:
            logger.error(f"Error connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        try:
            if self._redis:
                logger.info("Disconnecting from Redis server")
                await self._redis.close()
                self._redis = None
                logger.info("Disconnected from Redis server")
        except Exception as e:
            logger.error(f"Error disconnecting from Redis: {e}", exc_info=True)

    async def set(self, key: str, value: Any, expire: int = 0) -> bool:
        """
        Set a key-value pair in Redis
        
        Args:
            key: Redis key
            value: Any value (will be serialized to JSON)
            expire: Expiration time in seconds (0 for no expiration)
            
        Returns:
            True if successful
        """
        try:
            redis_client = await self.get_redis()
            value_str = json.dumps(value)
            result = await redis_client.set(key, value_str, ex=expire if expire > 0 else None)
            if result:
                if expire > 0:
                    logger.debug(f"Set Redis key '{key}' with expiration {expire}s")
                else:
                    logger.debug(f"Set Redis key '{key}' with no expiration")
            else:
                logger.warning(f"Failed to set Redis key '{key}'")
            return result
        except Exception as e:
            logger.error(f"Error setting key '{key}' in Redis: {e}", exc_info=True)
            return False
    
    async def get(self, key: str) -> Any:
        """
        Get a value from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Deserialized value or None if not found
        """
        try:
            redis_client = await self.get_redis()
            value = await redis_client.get(key)
            if value is not None:
                logger.debug(f"Retrieved Redis key '{key}'")
                return json.loads(value)
            else:
                logger.debug(f"Redis key '{key}' not found")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON from Redis key '{key}': {e}", exc_info=True)
            return None
        except Exception as e:
            logger.error(f"Error getting key '{key}' from Redis: {e}", exc_info=True)
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis
        
        Args:
            key: Redis key
            
        Returns:
            True if key was deleted, False if it didn't exist
        """
        try:
            redis_client = await self.get_redis()
            result = await redis_client.delete(key)
            if result > 0:
                logger.debug(f"Deleted Redis key '{key}'")
            else:
                logger.debug(f"Redis key '{key}' not found for deletion")
            return result > 0
        except Exception as e:
            logger.error(f"Error deleting key '{key}' from Redis: {e}", exc_info=True)
            return False

