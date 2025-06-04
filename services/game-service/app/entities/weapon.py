from abc import ABC, abstractmethod
from enum import Enum
from .entity import Entity
import logging

logger = logging.getLogger(__name__)


class WeaponType(Enum):
    BOMB = "bomb"
    BULLET = "bullet"
    MINE = "mine"


class Weapon(Entity, ABC):
    """Базовый класс для всех видов оружия"""
    
    def __init__(self, x: float, y: float, size: float, weapon_type: WeaponType, owner_id: str):
        super().__init__(x=x, y=y, width=size, height=size, name=f"Weapon_{weapon_type.value}")
        self.weapon_type: WeaponType = weapon_type
        self.owner_id: str = owner_id
        self.activated: bool = False
        self.timer: float = 0
        
        logger.debug(f"Weapon created: type={weapon_type.value}, position=({x}, {y}), owner={owner_id}")
    
    @abstractmethod
    def activate(self) -> None:
        """Активировать оружие (взрыв, выстрел и т.д.)"""
        pass
    
    @abstractmethod
    def update(self, delta_time: float) -> None:
        """Обновить состояние оружия"""
        pass
    
    @abstractmethod
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения в координатах сетки"""
        pass 