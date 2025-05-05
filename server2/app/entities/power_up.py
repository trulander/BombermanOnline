from enum import Enum
from .entity import Entity
from .player import Player # Keep for type hinting in apply_to_player

class PowerUpType(Enum):
    BOMB_UP = 'BOMB_UP'
    BOMB_POWER_UP = 'BOMB_POWER_UP'
    SPEED_UP = 'SPEED_UP'
    LIFE_UP = 'LIFE_UP'

class PowerUp(Entity):
    def __init__(self, x: float, y: float, size: float, power_type: PowerUpType):
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
        
    def apply_to_player(self, player: Player) -> None:
        if self.type == PowerUpType.BOMB_UP:
            player.max_bombs += 1
        elif self.type == PowerUpType.BOMB_POWER_UP:
            player.bomb_power += 1
        elif self.type == PowerUpType.SPEED_UP:
            player.speed += 0.5
            if player.speed > 6:
                player.speed = 6
        elif self.type == PowerUpType.LIFE_UP:
            player.lives += 1
