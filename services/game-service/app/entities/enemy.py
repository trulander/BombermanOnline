import random
from enum import Enum
from .entity import Entity

class EnemyType(Enum):
    COIN = "coin"
    BEAR = "bear"
    GHOST = "ghost"

class Enemy(Entity):
    ENEMY_LIVES: dict[EnemyType, int] = {
        EnemyType.COIN: 1,
        EnemyType.BEAR: 3,
        EnemyType.GHOST: 2,
    }

    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            speed: float,
            enemy_type: EnemyType
    ):
        super().__init__(
            x=x,
            y=y,
            width=size * 0.8,
            height=size * 0.8,
            speed=speed,
            ai=True,
            name=f"Enemy_{enemy_type.value}"
        )
        
        self.type: EnemyType = enemy_type
        self.lives: int = self.ENEMY_LIVES[enemy_type]

        # Movement
        self.move_timer: float = 0
        self.change_direction_interval: float = 1.0 + random.random() * 2.0
        
        # Initial random direction (normalized)
        self.direction: tuple[float, float] = self.get_random_direction()
        
        # State
        self.destroyed: bool = False
        self.destroy_animation_timer: float = 0

    def get_random_direction(self) -> tuple[float, float]:
        """Get a random normalized direction vector"""
        # Choose one of four cardinal directions
        choices = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        return random.choice(choices)