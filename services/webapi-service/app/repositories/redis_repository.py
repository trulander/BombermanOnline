import json
from typing import Any

import redis.asyncio as redis
from ..config import settings

class RedisRepository:
    """Repository for Redis"""
    
    def __init__(self) -> None:
        """Initialize Redis connection"""
        self.redis: redis.Redis = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    async def connect(self) -> None:
        """Connect to Redis"""
        # Redis connects on the first command, but we'll ping to check connection
        await self.redis.ping()
    
    async def disconnect(self) -> None:
        """Disconnect from Redis"""
        await self.redis.close()
    
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
        value_str = json.dumps(value)
        result = await self.redis.set(key, value_str, ex=expire if expire > 0 else None)
        return result
    
    async def get(self, key: str) -> Any:
        """
        Get a value from Redis
        
        Args:
            key: Redis key
            
        Returns:
            Deserialized value or None if not found
        """
        value = await self.redis.get(key)
        if value is not None:
            return json.loads(value)
        return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete a key from Redis
        
        Args:
            key: Redis key
            
        Returns:
            True if key was deleted, False if it didn't exist
        """
        result = await self.redis.delete(key)
        return result > 0

