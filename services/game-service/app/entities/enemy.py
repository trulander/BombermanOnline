import random
from enum import Enum
from .entity import Entity
import logging

logger = logging.getLogger(__name__)

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
    scale_size: float = 0.8

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
            width=size * self.scale_size,
            height=size * self.scale_size,
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
        
        logger.debug(f"Enemy created: type={enemy_type.value}, position=({x}, {y}), speed={speed}, lives={self.lives}")

    def get_random_direction(self) -> tuple[float, float]:
        """Get a random normalized direction vector"""
        try:
            # Choose one of four cardinal directions
            choices = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            direction = random.choice(choices)
            logger.debug(f"Enemy new direction: {direction}")
            return direction
        except Exception as e:
            logger.error(f"Error generating random direction: {e}", exc_info=True)
            # Fallback to a default direction
            return (0, 1)