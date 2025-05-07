from typing import TypedDict
from .entity import Entity

class PlayerInputs(TypedDict):
    up: bool
    down: bool
    left: bool
    right: bool
    bomb: bool

class Player(Entity):
    # Colors for different players
    COLORS: list[str] = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    def __init__(self, player_id: str):
        super().__init__(
            entity_id=player_id,
            width=32.0,
            height=32.0,
            speed=3.0,
            lives=3,
            color=self.COLORS[0] # Default color, will be assigned later
        )
        self.max_bombs: int = 1
        self.bomb_power: int = 1
        
        # Input state
        self.inputs: PlayerInputs = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'bomb': False
        }
    
    def set_inputs(self, inputs: dict) -> None:
        """Update player inputs"""
        for key, value in inputs.items():
            if key in self.inputs:
                self.inputs[key] = value