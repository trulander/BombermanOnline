from typing import TYPE_CHECKING

from app.entities import Player
from app.entities.player import UnitType
from app.entities.weapon import WeaponType
import logging

if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings


logger = logging.getLogger(__name__)


class Tank(Player):
    scale_size = 0.8
    unit_type: UnitType = UnitType.TANK

    def __init__(
            self,
            player_id: str,
            size: float,
            map: "Map",
            settings: "GameSettings",
    ):
        try:
            super().__init__(
                player_id=player_id,
                size=size,
                map=map,
                settings=settings
            )
            self.team_id: str | None = None
            self.direction: tuple[float, float] = (0, 1)

            # Настройки оружия в зависимости от типа юнита

            self.primary_weapon: WeaponType = WeaponType.BULLET
            self.primary_weapon_max_count: int = 1
            self.primary_weapon_power: int = 1

            self.secondary_weapon: WeaponType = WeaponType.MINE
            self.secondary_weapon_max_count: int = 1
            self.secondary_weapon_power: int = 1

            logger.info(f"Player created: id={player_id}, unit_type={self.unit_type.value}")
        except Exception as e:
            logger.error(f"Error creating player {player_id}: {e}", exc_info=True)
            raise

