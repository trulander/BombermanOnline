import logging
import time

from ..repositories.redis_repository import RedisRepository

logger = logging.getLogger(__name__)


class GameInstanceCache:
    def __init__(self, redis_repository: RedisRepository, ttl=60):
        self.redis_repository = redis_repository
        self.local_cache = {}
        self.ttl = ttl

    async def get_instance(self, game_id: str):
        # Проверяем локальный кэш
        if game_id in self.local_cache and time.time() - self.local_cache[game_id]["timestamp"] < self.ttl:
            return self.local_cache[game_id]["instance_id"]

        # Проверяем Redis
        instance_id = await self.redis_repository.get(key=f"games:{game_id}")
        if instance_id:
            await self.redis_repository.set(key=f"games:{game_id}", expire=self.ttl + 10, value=instance_id)
            self.local_cache[game_id] = {
                "instance_id": instance_id,
                "timestamp": time.time()
            }
            return instance_id
        return None

    async def set_instance(self, game_id: str, instance_id: str):
        # Сохраняем в Redis с TTL
        await self.redis_repository.set(key=f"games:{game_id}", expire=self.ttl+10, value=instance_id)
        # Обновляем локальный кэш
        self.local_cache[game_id] = {"instance_id": instance_id, "timestamp": time.time()}