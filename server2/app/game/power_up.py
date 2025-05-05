from enum import Enum

from app.game.player import Player


class PowerUpType(Enum):
    BOMB_UP = 'BOMB_UP'
    BOMB_POWER_UP = 'BOMB_POWER_UP'
    SPEED_UP = 'SPEED_UP'
    LIFE_UP = 'LIFE_UP'

class PowerUp:
    def __init__(self, x: float, y: float, size: int, power_type: PowerUpType):
        self.x: float = x
        self.y: float = y
        self.width: int = size * 0.7
        self.height: int = size * 0.7
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
