from app.entities import Player
from app.entities.player import UnitType
from app.entities.weapon import WeaponType
import logging

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings

logger = logging.getLogger(__name__)

class Bomberman(Player):

    scale_size = 0.8
    unit_type: UnitType = UnitType.BOMBERMAN

    def __init__(
            self,
            id: str,
            size: float,
            map: "Map",
            settings: "GameSettings",
            ai: bool = False,
    ):
        try:
            super().__init__(
                id=id,
                size = size,
                map=map,
                settings=settings,
                ai=ai
            )
            self.team_id: str | None = None
            self.direction: tuple[float, float] = (0, 1)

            # Настройки оружия в зависимости от типа юнита

            self.primary_weapon: WeaponType = WeaponType.BOMB
            self.primary_weapon_max_count: int = 1
            self.primary_weapon_power: int = 1

            self.secondary_weapon: WeaponType = None
            self.secondary_weapon_max_count: int = 1
            self.secondary_weapon_power: int = 1

            logger.info(f"Player created: id={id}, unit_type={self.unit_type.value}")
        except Exception as e:
            logger.error(f"Error creating player {id}: {e}", exc_info=True)
            raise


