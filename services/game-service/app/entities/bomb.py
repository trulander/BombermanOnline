from .weapon import Weapon, WeaponType
import logging

logger = logging.getLogger(__name__)

class Bomb(Weapon):
    weapon_type: WeaponType = WeaponType.BOMB

    def __init__(self, x: float, y: float, size: float, power: int, owner_id: str):
        super().__init__(x=x, y=y, size=size, owner_id=owner_id)
        self.power: int = power
        
        # Timing
        self.timer: float = 0
        self.exploded: bool = False
        self.explosion_timer: float = 0
        
        # Explosion cells will be populated when the bomb explodes
        self.explosion_cells: list[tuple[int, int]] = []
        
        logger.debug(f"Bomb created: position=({x}, {y}), power={power}, owner={owner_id}")
    
    def activate(self) -> None:
        """Активировать взрыв бомбы"""
        self.activated = True
        self.exploded = True
        logger.info(f"Bomb {self.id} exploded!")
    
    def update(self, delta_time: float) -> None:
        """Обновить состояние бомбы"""
        if self.exploded:
            self.explosion_timer += delta_time
        else:
            self.timer += delta_time
    
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения взрыва"""
        return self.explosion_cells.copy()