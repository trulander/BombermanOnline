from abc import ABC
from enum import Enum
from typing import TypedDict
from .entity import Entity
from .weapon import WeaponType
import logging


logger = logging.getLogger(__name__)


class PlayerInputs(TypedDict):
    up: bool
    down: bool
    left: bool
    right: bool
    weapon1: bool  # Основное оружие
    action1: bool  # дополнительное действие для оружия 1
    weapon2: bool  # Вторичное оружие


class UnitType(Enum):
    """Типы игровых юнитов"""
    BOMBERMAN = "bomberman"  # Классический бомбермен
    TANK = "tank"           # Танк с пулями


class Player(Entity, ABC):
    # Colors for different players
    COLORS: list[str] = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    # Input state
    inputs: PlayerInputs = {
        'up': False,
        'down': False,
        'left': False,
        'right': False,
        'weapon1': False,
        'action1': False,
        'weapon2': False
    }
    scale_size = 0.8
    unit_type: UnitType = None

    def __init__(self, player_id: str, size: float):
        try:
            super().__init__(
                entity_id=player_id,
                width=size * self.scale_size,
                height=size * self.scale_size,
                speed=3.0,
                lives=3,
                color=self.COLORS[0] # Default color, will be assigned later
            )
            self.team_id: str = ""  # ID команды
            self.direction: tuple[float, float] = (0, 1)  # Направление для танка

            # Настройки оружия в зависимости от типа юнита

            self.primary_weapon: WeaponType = WeaponType.BOMB
            self.primary_weapon_max_count: int = 1
            self.primary_weapon_power: int = 1

            self.secondary_weapon: WeaponType = None
            self.secondary_weapon_max_count: int = 1
            self.secondary_weapon_power: int = 1
            
            logger.info(f"Player created: id={player_id}, unit_type={self.unit_type.value}")
        except Exception as e:
            logger.error(f"Error creating player {player_id}: {e}", exc_info=True)
            raise
    
    def set_inputs(self, inputs: PlayerInputs) -> None:
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
    
    def set_team(self, team_id: str) -> None:
        """Назначить игрока в команду"""
        self.team_id = team_id
        logger.info(f"Player {self.id} assigned to team {team_id}")


