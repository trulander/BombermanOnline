from typing import TypedDict
from .entity import Entity
import logging

logger = logging.getLogger(__name__)

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
        try:
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
            
            logger.info(f"Player created: id={player_id}")
        except Exception as e:
            logger.error(f"Error creating player {player_id}: {e}", exc_info=True)
            raise
    
    def set_inputs(self, inputs: dict) -> None:
        """Update player inputs"""
        try:
            changed_inputs = []
            for key, value in inputs.items():
                if key in self.inputs and self.inputs[key] != value:
                    self.inputs[key] = value
                    changed_inputs.append(f"{key}={value}")
            
            if changed_inputs:
                logger.debug(f"Player {self.id} inputs updated: {', '.join(changed_inputs)}")
        except Exception as e:
            logger.error(f"Error setting inputs for player {self.id}: {e}", exc_info=True)