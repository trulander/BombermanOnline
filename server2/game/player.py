from typing import TypedDict, Optional

class PlayerInputs(TypedDict):
    up: bool
    down: bool
    left: bool
    right: bool
    bomb: bool

class Player:
    # Colors for different players
    COLORS: list[str] = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    def __init__(self, player_id: str):
        self.id: str = player_id
        self.x: float = 0
        self.y: float = 0
        self.width: int = 32  # Slightly smaller than cell size
        self.height: int = 32
        self.speed: float = 3
        self.max_bombs: int = 1
        self.bomb_power: int = 1
        self.lives: int = 3
        self.invulnerable: bool = False
        self.invulnerable_timer: float = 0
        self.color: str = self.COLORS[0]  # Default color, will be assigned based on player index
        
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