import random
from .entity import Entity

class Enemy(Entity):
    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            speed: float
    ):
        super().__init__(
            x=x,
            y=y,
            width=size * 0.8,
            height=size * 0.8,
            speed=speed,
            ai=True,
            name="Enemy"
        )
        
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