import random
from enum import Enum
from typing import TYPE_CHECKING, NotRequired, TypedDict

from typer.cli import state

from .entity import Entity
import logging

if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings



logger = logging.getLogger(__name__)

class EnemyType(Enum):
    COIN = "coin"
    BEAR = "bear"
    GHOST = "ghost"

class EnemyUpdate(TypedDict):
    entity_id: str
    x: NotRequired[float]
    y: NotRequired[float]
    type: NotRequired[EnemyType]
    lives: NotRequired[int]
    invulnerable: NotRequired[bool]
    destroyed: NotRequired[bool]


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
            enemy_type: EnemyType,
            map: "Map",
            settings: "GameSettings",
    ):
        super().__init__(
            x=x,
            y=y,
            width=size * self.scale_size,
            height=size * self.scale_size,
            speed=speed,
            ai=True,
            name=f"Enemy_{enemy_type.value}",
            map=map,
            settings=settings
        )
        
        self.type: EnemyType = enemy_type
        self.lives: int = self.ENEMY_LIVES[enemy_type]


        logger.debug(f"Enemy created: type={enemy_type.value}, position=({x}, {y}), speed={speed}, lives={self.lives}")

    def get_changes(self, full_state: bool = False) -> EnemyUpdate:
        previous_state = {} if full_state else getattr(self, "_state", {})
        current_state = {
            "x": self.x,
            "y": self.y,
            "type": self.type,
            "lives": self.lives,
            "invulnerable": self.invulnerable,
            "destroyed": self.destroyed,
        }
        changes = {
            "entity_id": self.id
        }
        for key, value in current_state.items():
            if key not in previous_state or previous_state[key] != value:
                changes[key] = value
        self._state = current_state
        return EnemyUpdate(**changes)
