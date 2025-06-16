import random
import time

from .weapon import Weapon, WeaponType
import logging

logger = logging.getLogger(__name__)

class Bomb(Weapon):
    weapon_type: WeaponType = WeaponType.BOMB
    scale_size = 0.8


    def __init__(self, x: float, y: float, size: float, power: int, owner_id: str):
        super().__init__(x=x, y=y, size=size, owner_id=owner_id)
        self.power: int = power
        
        logger.debug(f"Bomb created: position=({x}, {y}), power={power}, owner={owner_id}, timer={self.time_created}")


    def activate(self, **kwargs) -> None:
        """Активировать взрыв бомбы"""
        super().activate(kwargs=kwargs)
        logger.info(f"Bomb {self.id} exploded!")

    
    def update(self, *kwargs) -> None:
        """Обновить состояние бомбы"""
        super().update(kwargs=kwargs)

    
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения взрыва"""
        return super().get_damage_area()