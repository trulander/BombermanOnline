import random

class Enemy:
    def __init__(self, x, y, size, speed):
        self.x = x
        self.y = y
        self.width = size * 0.8
        self.height = size * 0.8
        self.speed = speed
        
        # Position enemy in center of cell
        self.x += (size - self.width) / 2
        self.y += (size - self.height) / 2
        
        # Movement
        self.direction = self.get_random_direction()
        self.move_timer = 0
        self.change_direction_interval = 1.5
        
        # State
        self.destroyed = False
        self.destroy_animation_timer = 0
    
    def get_random_direction(self):
        """Get a random direction for movement"""
        if random.random() < 0.5:
            return (random.choice([-1, 1]), 0)
        else:
            return (0, random.choice([-1, 1]))
