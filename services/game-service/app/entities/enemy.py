import random
from enum import Enum
from typing import TYPE_CHECKING

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
