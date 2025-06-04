from . import GameSettings
from .weapon import Weapon, WeaponType
import logging

logger = logging.getLogger(__name__)

class Bullet(Weapon):
    def __init__(self, x: float, y: float, size: float, direction: tuple[float, float], speed: float, owner_id: str):
        super().__init__(x=x, y=y, size=size, weapon_type=WeaponType.BULLET, owner_id=owner_id)
        self.direction: tuple[float, float] = direction  # Нормализованный вектор направления
        self.speed: float = speed
        self.hit_target: bool = False
        
        logger.debug(f"Bullet created: position=({x}, {y}), direction={direction}, speed={speed}, owner={owner_id}")
    
    def activate(self) -> None:
        """Пуля активируется при попадании в цель"""
        self.activated = True
        self.hit_target = True
        logger.debug(f"Bullet {self.id} hit target!")
    
    def update(self, delta_time: float) -> None:
        """Обновить положение пули"""
        if not self.hit_target:
            # Двигаем пулю в направлении
            dx = self.direction[0] * self.speed * delta_time * 60
            dy = self.direction[1] * self.speed * delta_time * 60
            self.x += dx
            self.y += dy
        
        self.timer += delta_time
    
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить текущую позицию пули в координатах сетки"""
        grid_x = int((self.x + self.width/2) / GameSettings.cell_size)
        grid_y = int((self.y + self.height/2) / GameSettings.cell_size)
        return [(grid_x, grid_y)] 