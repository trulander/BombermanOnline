from typing import Any
from redis.asyncio import Redis
from .import BaseRepository
from ..config import settings

class RedisRepository(BaseRepository[Any]):
    """Репозиторий для работы с Redis"""
    
    def __init__(self) -> None:
        self.redis: Redis | None = None
    
    async def connect(self) -> None:
        """Установить соединение с Redis"""
        self.redis = Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD,
            decode_responses=True
        )
    
    async def disconnect(self) -> None:
        """Закрыть соединение с Redis"""
        if self.redis:
            await self.redis.close()
    
    async def get(self, id: str) -> Any | None:
        """Получить значение по ключу"""
        if not self.redis:
            await self.connect()
        return await self.redis.get(id)
    
    async def create(self, data: Any) -> Any:
        """Сохранить значение в Redis"""
        if not self.redis:
            await self.connect()
        await self.redis.set(str(id(data)), str(data))
        return data
    
    async def update(self, id: str, data: Any) -> Any | None:
        """Обновить значение в Redis"""
        if not self.redis:
            await self.connect()
        exists = await self.redis.exists(id)
        if exists:
            await self.redis.set(id, str(data))
            return data
        return None
    
    async def delete(self, id: str) -> bool:
        """Удалить значение из Redis"""
        if not self.redis:
            await self.connect()
        return bool(await self.redis.delete(id))