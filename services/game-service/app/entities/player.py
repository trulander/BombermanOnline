from typing import TypedDict
from .entity import Entity
from .unit_type import UnitType
from .weapon import WeaponType
import logging

logger = logging.getLogger(__name__)

class PlayerInputs(TypedDict):
    up: bool
    down: bool
    left: bool
    right: bool
    weapon1: bool  # Основное оружие
    weapon2: bool  # Вторичное оружие

class Player(Entity):
    # Colors for different players
    COLORS: list[str] = ['#3498db', '#e74c3c', '#2ecc71', '#f39c12']
    
    def __init__(self, player_id: str, unit_type: UnitType = UnitType.BOMBERMAN):
        try:
            super().__init__(
                entity_id=player_id,
                width=32.0,
                height=32.0,
                speed=3.0,
                lives=3,
                color=self.COLORS[0] # Default color, will be assigned later
            )
            self.unit_type: UnitType = unit_type
            self.team_id: str = ""  # ID команды
            self.direction: tuple[float, float] = (0, 1)  # Направление для танка
            
            # Настройки оружия в зависимости от типа юнита
            if unit_type == UnitType.BOMBERMAN:
                self.primary_weapon: WeaponType = WeaponType.BOMB
                self.secondary_weapon: WeaponType = WeaponType.MINE
                self.max_weapons: int = 1  # Максимальное количество активного оружия
                self.weapon_power: int = 1
            elif unit_type == UnitType.TANK:
                self.primary_weapon: WeaponType = WeaponType.BULLET
                self.secondary_weapon: WeaponType = WeaponType.MINE
                self.max_weapons: int = 10  # Танк может стрелять много пуль
                self.weapon_power: int = 1
            
            # Input state
            self.inputs: PlayerInputs = {
                'up': False,
                'down': False,
                'left': False,
                'right': False,
                'weapon1': False,
                'weapon2': False
            }
            
            logger.info(f"Player created: id={player_id}, unit_type={unit_type.value}")
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
    
    # Поддержка старых свойств для совместимости
    @property
    def max_bombs(self) -> int:
        return self.max_weapons if self.primary_weapon == WeaponType.BOMB else 0
    
    @max_bombs.setter
    def max_bombs(self, value: int) -> None:
        if self.primary_weapon == WeaponType.BOMB:
            self.max_weapons = value
    
    @property
    def bomb_power(self) -> int:
        return self.weapon_power
    
    @bomb_power.setter
    def bomb_power(self, value: int) -> None:
        self.weapon_power = value