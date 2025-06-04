from . import GameSettings
from .weapon import Weapon, WeaponType
import logging

logger = logging.getLogger(__name__)

class Mine(Weapon):
    def __init__(self, x: float, y: float, size: float, owner_id: str):
        super().__init__(x=x, y=y, size=size, weapon_type=WeaponType.MINE, owner_id=owner_id)
        self.exploded: bool = False
        self.triggered: bool = False
        
        logger.debug(f"Mine created: position=({x}, {y}), owner={owner_id}")
    
    def activate(self) -> None:
        """Активировать взрыв мины"""
        self.activated = True
        self.exploded = True
        logger.info(f"Mine {self.id} exploded!")
    
    def trigger(self) -> None:
        """Триггер мины при наступлении на неё"""
        if not self.triggered:
            self.triggered = True
            logger.debug(f"Mine {self.id} triggered!")
    
    def update(self, delta_time: float) -> None:
        """Обновить состояние мины"""
        self.timer += delta_time
        
        # Мина взрывается через некоторое время после триггера
        if self.triggered and self.timer >= 1.0 and not self.exploded:
            self.activate()
    
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения мины (3x3 область)"""
        if not self.exploded:
            return []
        
        grid_x = int((self.x + self.width/2) / GameSettings.cell_size)
        grid_y = int((self.y + self.height/2) / GameSettings.cell_size)
        
        damage_area = []
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                damage_area.append((grid_x + dx, grid_y + dy))
        
        return damage_area 