import random

class Enemy:
    def __init__(self, x: float, y: float, size: int, speed: float):
        self.id: int = None
        self.x: float = x
        self.y: float = y
        self.width: int = size * 0.8
        self.height: int = size * 0.8
        self.speed: float = speed
        
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