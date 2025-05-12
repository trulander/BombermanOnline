from .entity import Entity
import logging

logger = logging.getLogger(__name__)

class Bomb(Entity):
    def __init__(self, x: float, y: float, size: float, power: int, owner_id: str):
        super().__init__(x=x, y=y, width=size, height=size, name="Bomb")
        self.power: int = power
        self.owner_id: str = owner_id
        
        # Timing
        self.timer: float = 0
        self.exploded: bool = False
        self.explosion_timer: float = 0
        
        # Explosion cells will be populated when the bomb explodes
        self.explosion_cells: list[tuple[int, int]] = []
        
        logger.debug(f"Bomb created: position=({x}, {y}), power={power}, owner={owner_id}")