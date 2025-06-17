from .weapon import Weapon, WeaponType
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings


logger = logging.getLogger(__name__)

class Bullet(Weapon):
    weapon_type: WeaponType = WeaponType.BULLET
    scale_size = 0.3


    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            speed: float,
            owner_id: str,
            direction: tuple[float, float],
            map: "Map",
            settings: "GameSettings",
    ):
        super().__init__(
            x=x,
            y=y,
            size=size,
            owner_id=owner_id,
            map=map,
            settings=settings
        )
        self.direction: tuple[float, float] = direction  # Нормализованный вектор направления
        self.speed: float = speed
        self.power: int = 1
        logger.debug(f"Bullet created: position=({x}, {y}), direction={direction}, speed={speed}, owner={owner_id}")
    

    def activate(self, **kwargs) -> None:
        """Пуля активируется при попадании в цель"""
        super().activate(kwargs=kwargs)
        logger.debug(f"Bullet {self.id} hit target!")


    def update(self, **kwargs) -> None:
        """Обновить положение пули"""
        if not self.move(
                delta_time=kwargs.get('delta_time', 0)
        ):
            self.activate(kwargs=kwargs)


    def get_direction(self) -> tuple[float, float]:
        """Get a random normalized direction vector"""
        try:
            return self.direction
        except Exception as e:
            logger.error(f"Error getting bullets direction: {e}", exc_info=True)
            # Fallback to a default direction
            return (0, 1)


    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить текущую позицию пули в координатах сетки"""
        return super().get_damage_area()

