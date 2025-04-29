from enum import Enum

class PowerUpType(Enum):
    BOMB_UP = 'BOMB_UP'
    POWER_UP = 'POWER_UP'
    LIFE_UP = 'LIFE_UP'
    SPEED_UP = 'SPEED_UP'

class PowerUp:
    def __init__(self, x, y, size, power_up_type):
        self.x = x
        self.y = y
        self.width = size * 0.7
        self.height = size * 0.7
        self.type = power_up_type
        
        # Center powerup in cell
        self.x += (size - self.width) / 2
        self.y += (size - self.height) / 2
