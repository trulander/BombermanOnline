from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic

from .redis_repository import RedisRepository

T = TypeVar('T')

class BaseRepository(ABC, Generic[T]):
    """Базовый класс для всех репозиториев"""
    
    @abstractmethod
    async def get(self, id: str) -> T | None:
        """Получить объект по идентификатору"""
        pass
    
    @abstractmethod
    async def create(self, data: T) -> T:
        """Создать новый объект"""
        pass
    
    @abstractmethod
    async def update(self, id: str, data: T) -> T | None:
        """Обновить существующий объект"""
        pass
    
    @abstractmethod
    async def delete(self, id: str) -> bool:
        """Удалить объект"""
        pass 