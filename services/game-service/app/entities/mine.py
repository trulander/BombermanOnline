from typing import TYPE_CHECKING

from .weapon import Weapon, WeaponType
import logging
if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings


logger = logging.getLogger(__name__)

class Mine(Weapon):
    weapon_type: WeaponType = WeaponType.MINE
    scale_size = 0.8


    def __init__(
            self,
            x: float,
            y: float,
            size: float,
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
        self.power: int = 1
        logger.debug(f"Mine created: position=({x}, {y}), owner={owner_id}")


    def activate(self, **kwargs) -> None:
        """Активировать взрыв мины"""
        super().activate(**kwargs)
        logger.info(f"Mine {self.id} exploded!")

    
    def update(self, **kwargs) -> None:
        """Обновить состояние мины"""
        super().update(**kwargs)


    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения мины (3x3 область)"""
        return super().get_damage_area()