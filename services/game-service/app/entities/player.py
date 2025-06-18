from abc import ABC
from enum import Enum
from typing import TYPE_CHECKING

from .entity import Entity
from .weapon import WeaponType
import logging

if TYPE_CHECKING:
    from . import Inputs
    from . import Map
    from ..models.game_models import GameSettings

logger = logging.getLogger(__name__)


class UnitType(Enum):
    """Типы игровых юнитов"""
    BOMBERMAN = "bomberman"  # Классический бомбермен
    TANK = "tank"           # Танк с пулями


class Player(Entity, ABC):
    # Colors for different players
    COLORS: list[str] = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    # Input state

    scale_size = 0.8
    unit_type: UnitType = None

    def __init__(
            self,
            player_id: str,
            size: float,
            map: "Map",
            settings: "GameSettings",
            name: str = None,
    ):
        try:
            super().__init__(
                entity_id=player_id,
                width=size * self.scale_size,
                height=size * self.scale_size,
                speed=3.0,
                lives=3,
                color=self.COLORS[0], # Default color, will be assigned later
                map = map,
                settings = settings
            )
            self.team_id: str = ""  # ID команды


            # Настройки оружия в зависимости от типа юнита

            self.primary_weapon: WeaponType = WeaponType.BOMB
            self.primary_weapon_max_count: int = 1
            self.primary_weapon_power: int = 1

            self.secondary_weapon: WeaponType = None
            self.secondary_weapon_max_count: int = 1
            self.secondary_weapon_power: int = 1

            self.inputs: "Inputs" = {
                'up': False,
                'down': False,
                'left': False,
                'right': False,
                'weapon1': False,
                'action1': False,
                'weapon2': False
            }
            
            logger.info(f"Player created: id={player_id}, unit_type={self.unit_type.value}")
        except Exception as e:
            logger.error(f"Error creating player {player_id}: {e}", exc_info=True)
            raise
    
    def set_inputs(self, inputs: "Inputs") -> None:
        """Update player inputs"""
        try:
            changed_inputs = []
            for key, value in inputs.items():
                if key in self.inputs and self.inputs[key] != value:
                    self.inputs[key] = value
                    changed_inputs.append(f"{key}={value}")
            
            # Обновляем направление для танка на основе движения
            if self.unit_type == UnitType.TANK:
                if self.inputs.get('up'):
                    self.direction = (0, -1)
                elif self.inputs.get('down'):
                    self.direction = (0, 1)
                elif self.inputs.get('left'):
                    self.direction = (-1, 0)
                elif self.inputs.get('right'):
                    self.direction = (1, 0)
            
            if changed_inputs:
                logger.debug(f"Player {self.id} inputs updated: {', '.join(changed_inputs)}")
        except Exception as e:
            logger.error(f"Error setting inputs for player {self.id}: {e}", exc_info=True)


    def get_direction(self) -> tuple[float, float]:
        # Обработка движения
        dx: float = 0
        dy: float = 0
        # рассчет движения игрока
        if self.inputs.get('up'):
            dy = -1
        if self.inputs.get('down'):
            dy = 1
        if self.inputs.get('left'):
            dx = -1
        if self.inputs.get('right'):
            dx = 1

        return (dx, dy)


    def set_team(self, team_id: str) -> None:
        """Назначить игрока в команду"""
        self.team_id = team_id
        logger.info(f"Player {self.id} assigned to team {team_id}")


    def update_player_weapon(self, weapon_type: WeaponType, count: int, power: float):
        if self.primary_weapon == weapon_type:
            self.primary_weapon_max_count += count
            self.primary_weapon_power += power
        elif self.secondary_weapon == weapon_type:
            self.secondary_weapon_max_count += count
            self.secondary_weapon_power += power


    def update_player_params(self, speed: float = 0, lives: int = 0):
        self.speed += speed
        if self.speed>= self.settings.player_max_speed:
            self.speed = self.settings.player_max_speed
        self.lives += lives
        if self.lives >= self.settings.player_max_lives:
            self.lives = self.settings.player_max_lives


