import random
import time


from .weapon import Weapon, WeaponType
import logging

from typing import TYPE_CHECKING
from . import CellType

if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings



logger = logging.getLogger(__name__)

class Bomb(Weapon):
    weapon_type: WeaponType = WeaponType.BOMB
    scale_size = 0.8


    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            power: int,
            owner_id: str,
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
        self.power: int = power
        map.set_cell_type(
            x=int(self.x / self.settings.cell_size),
            y=int(self.y / self.settings.cell_size),
            cell_type=CellType.BLOCKED_BOMB
        )
        self._fill_explosion_area_geometry()

        logger.debug(f"Bomb created: position=({x}, {y}), power={power}, owner={owner_id}, timer={self.settings.bomb_timer}")


    def activate(self, **kwargs) -> None:
        """Активировать взрыв бомбы"""
        super().activate(**kwargs)
        self.map.set_cell_type(
            x=int(self.x / self.settings.cell_size),
            y=int(self.y / self.settings.cell_size),
            cell_type=CellType.EMPTY
        )
        logger.info(f"Bomb {self.id} exploded!")

    
    def update(self, **kwargs) -> None:
        """Обновить состояние бомбы"""
        super().update(**kwargs)

    
    def get_damage_area(self) -> set[tuple[int, int]]:
        """Получить область поражения взрыва"""
        return super().get_damage_area()