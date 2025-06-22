from enum import Enum
from typing import TYPE_CHECKING, TypedDict, NotRequired

from .entity import Entity
from .player import Player # Keep for type hinting in apply_to_player
import logging

from .weapon import WeaponType

if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings



logger = logging.getLogger(__name__)


class PowerUpType(Enum):
    BOMB_UP = 'BOMB_UP'
    BULLET_UP = 'BULLET_UP'
    MINE_UP = 'MINE_UP'
    BOMB_POWER_UP = 'BOMB_POWER_UP'
    BULLET_POWER_UP = 'BULLET_POWER_UP'# bullet speed up
    # MINE_POWER_UP = 'MINE_POWER_UP'
    SPEED_UP = 'SPEED_UP'
    LIFE_UP = 'LIFE_UP'


class PowerUpUpdate(TypedDict):
    entity_id: str
    x: NotRequired[float]
    y: NotRequired[float]
    type: NotRequired[PowerUpType]


class PowerUp(Entity):
    scale_size = 0.7
    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            power_type: PowerUpType,
            map: "Map",
            settings: "GameSettings",
    ):
        try:
            width = size * self.scale_size
            height = size * self.scale_size
            super().__init__(
                x=x + (size - width) / 2,
                y=y + (size - height) / 2,
                width=width,
                height=height,
                name=f"PowerUp_{power_type.name}",
                map=map,
                settings=settings
            )
            self.type: PowerUpType = power_type
            logger.debug(f"PowerUp created: type={power_type.name}, position=({self.x}, {self.y})")
        except Exception as e:
            logger.error(f"Error creating PowerUp at ({x}, {y}): {e}", exc_info=True)
            raise

    def apply_to_player(self, player: Player) -> None:
        try:
            match self.type:
                case PowerUpType.BOMB_UP:
                    player.update_player_weapon(weapon_type=WeaponType.BOMB, count=1, power=0)
                case PowerUpType.BULLET_UP:
                    player.update_player_weapon(weapon_type=WeaponType.BULLET, count=1, power=0)
                case PowerUpType.MINE_UP:
                    player.update_player_weapon(weapon_type=WeaponType.MINE, count=1, power=0)
                case PowerUpType.BOMB_POWER_UP:
                    player.update_player_weapon(weapon_type=WeaponType.BOMB, count=0, power=1)
                case PowerUpType.BULLET_POWER_UP:
                    player.update_player_weapon(weapon_type=WeaponType.BULLET, count=0, power=1)
                # case PowerUpType.MINE_POWER_UP:
                #     player.update_player_weapon(weapon_type=WeaponType.MINE, count=0, power=1)
                case PowerUpType.SPEED_UP:
                    player.update_player_params(speed=0.5)
                    logger.info(f"Player {player.id} received SPEED_UP. New speed: {player.speed}")
                case PowerUpType.LIFE_UP:
                    player.update_player_params(lives=1)
                    logger.info(f"Player {player.id} received LIFE_UP. New lives: {player.lives}")

        except Exception as e:
            logger.error(f"Error applying powerup {self.type.name} to player {player.id}: {e}", exc_info=True)

    def get_changes(self, full_state: bool = False) -> PowerUpUpdate:
        previous_state = {} if full_state else getattr(self, "_state", {})
        current_state = {
            "x": self.x,
            "y": self.y,
            "type": self.type
        }
        changes = {
            "entity_id": self.id
        }
        for key, value in current_state.items():
            if key not in previous_state or previous_state[key] != value:
                changes[key] = value
        self._state = current_state
        return PowerUpUpdate(**changes)