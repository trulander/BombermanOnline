from enum import Enum
from .entity import Entity
from .player import Player # Keep for type hinting in apply_to_player
import logging

logger = logging.getLogger(__name__)

class PowerUpType(Enum):
    BOMB_UP = 'BOMB_UP'
    BOMB_POWER_UP = 'BOMB_POWER_UP'
    SPEED_UP = 'SPEED_UP'
    LIFE_UP = 'LIFE_UP'

class PowerUp(Entity):
    def __init__(self, x: float, y: float, size: float, power_type: PowerUpType):
        try:
            width = size * 0.7
            height = size * 0.7
            super().__init__(
                x=x + (size - width) / 2,
                y=y + (size - height) / 2,
                width=width,
                height=height,
                name=f"PowerUp_{power_type.name}"
            )
            self.type: PowerUpType = power_type
            logger.debug(f"PowerUp created: type={power_type.name}, position=({self.x}, {self.y})")
        except Exception as e:
            logger.error(f"Error creating PowerUp at ({x}, {y}): {e}", exc_info=True)
            raise
        
    def apply_to_player(self, player: Player) -> None:
        try:
            if self.type == PowerUpType.BOMB_UP:
                player.max_bombs += 1
                logger.info(f"Player {player.id} received BOMB_UP. New max bombs: {player.max_bombs}")
            elif self.type == PowerUpType.BOMB_POWER_UP:
                player.bomb_power += 1
                logger.info(f"Player {player.id} received BOMB_POWER_UP. New bomb power: {player.bomb_power}")
            elif self.type == PowerUpType.SPEED_UP:
                player.speed += 0.5
                if player.speed > 6:
                    player.speed = 6
                logger.info(f"Player {player.id} received SPEED_UP. New speed: {player.speed}")
            elif self.type == PowerUpType.LIFE_UP:
                player.lives += 1
                logger.info(f"Player {player.id} received LIFE_UP. New lives: {player.lives}")
        except Exception as e:
            logger.error(f"Error applying powerup {self.type.name} to player {player.id}: {e}", exc_info=True)
