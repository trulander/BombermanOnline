class Bomb:
    def __init__(self, x: float, y: float, size: int, power: int, owner_id: str):
        self.x: float = x
        self.y: float = y
        self.width: int = size
        self.height: int = size
        self.power: int = power
        self.owner_id: str = owner_id
        
        # Timing
        self.timer: float = 0
        self.exploded: bool = False
        self.explosion_timer: float = 0
        
        # Explosion cells will be populated when the bomb explodes
        self.explosion_cells: list[tuple[int, int]] = [] 