class Bomb:
    def __init__(self, x, y, size, power, owner_id):
        self.x = x
        self.y = y
        self.width = size
        self.height = size
        self.power = power
        self.owner_id = owner_id
        
        # Timing
        self.timer = 0
        self.exploded = False
        self.explosion_timer = 0
        
        # Explosion cells will be populated when the bomb explodes
        self.explosion_cells = []
