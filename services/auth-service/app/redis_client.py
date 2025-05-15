import redis.asyncio as redis
import logging
import json
from typing import Any
from .config import settings

logger = logging.getLogger(__name__)

class RedisClient:
    def __init__(self) -> None:
        self.client = None
    
    async def connect(self) -> None:
        """Подключение к Redis"""
        try:
            self.client = redis.Redis = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD,
                decode_responses=True
            )
            # Проверяем соединение
            await self.client.ping()
            logger.info("Connected to Redis successfully")
        except Exception as e:
            logger.error(f"Error connecting to Redis: {e}", exc_info=True)
            raise
    
    async def disconnect(self) -> None:
        """Отключение от Redis"""
        if self.client:
            try:
                await self.client.close()
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}", exc_info=True)
                raise
    
    async def get(self, key: str) -> Any:
        """Получение данных из Redis"""
        try:
            data = await self.client.get(key)
            if data:
                try:
                    return json.loads(data)
                except json.JSONDecodeError:
                    return data
            return None
        except Exception as e:
            logger.error(f"Error getting data from Redis: {e}", exc_info=True)
            return None
    
    async def set(self, key: str, value: Any, expire: int = None) -> bool:
        """Сохранение данных в Redis"""
        try:
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            if expire:
                return await self.client.setex(key, expire, value)
            else:
                return await self.client.set(key, value)
        except Exception as e:
            logger.error(f"Error setting data to Redis: {e}", exc_info=True)
            return False
    
    async def delete(self, key: str) -> int:
        """Удаление данных из Redis"""
        try:
            return await self.client.delete(key)
        except Exception as e:
            logger.error(f"Error deleting data from Redis: {e}", exc_info=True)
            return 0
    
    async def exists(self, key: str) -> bool:
        """Проверка существования ключа в Redis"""
        try:
            return await self.client.exists(key) > 0
        except Exception as e:
            logger.error(f"Error checking key existence in Redis: {e}", exc_info=True)
            return False
    
    async def block_token(self, token: str, expire: int) -> bool:
        """Добавление токена в черный список"""
        key = f"blacklisted_token:{token}"
        return await self.set(key, "1", expire)
    
    async def is_token_blacklisted(self, token: str) -> bool:
        """Проверка токена в черном списке"""
        key = f"blacklisted_token:{token}"
        return await self.exists(key)

redis_client = RedisClient() 