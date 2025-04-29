from enum import Enum

class PowerUpType(Enum):
    EXTRA_BOMB = 1
    BOMB_POWER = 2
    SPEED = 3

class PowerUp:
    def __init__(self, x: float, y: float, size: int, power_type: PowerUpType):
        self.x: float = x
        self.y: float = y
        self.width: int = size
        self.height: int = size
        self.type: PowerUpType = power_type
        
    def apply_to_player(self, player) -> None:
        if self.type == PowerUpType.EXTRA_BOMB:
            player.max_bombs += 1
        elif self.type == PowerUpType.BOMB_POWER:
            player.bomb_power += 1
        elif self.type == PowerUpType.SPEED:
            player.speed += 0.5 