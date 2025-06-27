import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Callable, TYPE_CHECKING, TypedDict, NotRequired
from .entity import Entity
import logging

if TYPE_CHECKING:
    from . import Map
    from ..models.game_models import GameSettings



logger = logging.getLogger(__name__)


class WeaponType(Enum):
    BOMB = "BOMB"
    BULLET = "BULLET"
    MINE = "MINE"

class WeaponAction(Enum):
    PLACEWEAPON1 = "PLACEWEAPON1"
    WEAPON1ACTION1 = "WEAPON1ACTION1"
    PLACEWEAPON2 = "PLACEWEAPON2"

class WeaponUpdate(TypedDict):
    entity_id: str
    x: NotRequired[float]
    y: NotRequired[float]
    weapon_type: NotRequired[WeaponType]
    direction: NotRequired[tuple[float, float]]
    activated: NotRequired[bool]
    exploded: NotRequired[bool]
    explosion_cells: NotRequired[list[tuple[int, int]]]
    owner_id: NotRequired[str]


class Weapon(Entity, ABC):
    """Базовый класс для всех видов оружия"""
    weapon_type: WeaponType = None
    scale_size = 0.8


    def __init__(
            self,
            x: float,
            y: float,
            size: float,
            owner_id: str,
            map: "Map",
            settings: "GameSettings",
            direction: tuple[float, float] = (0, 1)
    ):
        super().__init__(
            x=x,
            y=y,
            width=size * self.scale_size,
            height=size * self.scale_size,
            name=f"Weapon_{self.weapon_type.value}",
            map=map,
            settings=settings
        )
        self.power: int = 1 # значение по умолчанию

        self.direction: tuple[float, float] = direction
        self.owner_id: str = owner_id

        self.activated: bool = False
        # self.exploded: bool = False

        self.timer: float = 0#self.settings.bomb_timer # По умолчанию таймер для бомбы, может быть переопределен в другом оружии
        # self.exploded: bool = False
        self.activated_timer: float = 0

        # Explosion cells will be populated when the bomb explodes
        self.explosion_cells_grid: list[tuple[int, int]] = []
        self.explosion_cells: list[tuple[int, int]] = []
        #блоки разрушенные при взрыве.
        self.destroyed_blocks: list[tuple[int, int]] = []
        
        logger.debug(f"Weapon created: type={self.weapon_type.value}, position=({x}, {y}), owner={owner_id}")


    def activate(self, **kwargs) -> bool:
        """Активировать оружие (взрыв, выстрел и т.д.)"""
        if not self.activated:
            self.calc_explosion_area()
            handle_weapon_explosion: Callable = kwargs.get('handle_weapon_explosion')
            self.activated = True

            if handle_weapon_explosion:
                handle_weapon_explosion(self)
            return True
        return False


    def update(self, **kwargs) -> None:
        """Обновить состояние оружия, по умолчанию бомбы"""
        # handle_weapon_explosion: Callable = kwargs.get('handle_weapon_explosion')
        self.timer += kwargs['delta_time']

        if not self.activated and self.timer >= self.settings.bomb_timer:
            self.activate(**kwargs)
        elif self.activated:
            self.activated_timer += kwargs.get("delta_time", 0)

    
    def get_damage_area(self) -> list[tuple[int, int]]:
        """Получить область поражения взрыва"""
        if self.activated:
            return self.explosion_cells_grid
        return []


    def get_destroyed_blocks(self) -> list[tuple[int, int]]:
        if self.activated:
            return self.destroyed_blocks
        return []


    def calc_explosion_area(self):
        # Получаем координаты бомбы в сетке
        grid_x: int = int(self.x / self.settings.cell_size)
        grid_y: int = int(self.y / self.settings.cell_size)

        # Добавляем центр взрыва
        self.explosion_cells_grid.append((grid_x, grid_y))
        self.explosion_cells.append((grid_x * self.settings.cell_size, grid_y * self.settings.cell_size))

        # Проверяем в каждом из четырех направлений
        directions: list[tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]

        for dx, dy in directions:
            for i in range(1, self.power + 1):
                check_x: int = grid_x + (dx * i)
                check_y: int = grid_y + (dy * i)

                # Останавливаемся при попадании в стену
                if self.map.is_wall(check_x, check_y):
                    break

                self.explosion_cells_grid.append((check_x, check_y))
                self.explosion_cells.append((check_x * self.settings.cell_size, check_y * self.settings.cell_size))

                # Если попали в разрушаемый блок, разрушаем его и останавливаем взрыв
                if self.map.is_breakable_block(check_x, check_y):
                    if self.map.destroy_block(check_x, check_y):
                        self.destroyed_blocks.append((check_x, check_y))
                    break


    def is_exploded(self) -> bool:
        if self.activated and self.activated_timer >= self.settings.bomb_explosion_duration:
            return True
        return False

    def get_changes(self, full_state: bool = False) -> WeaponUpdate:
        previous_state = {} if full_state else getattr(self, "_state", {})
        current_state = {
            "x": self.x,
            "y": self.y,
            "weapon_type": self.weapon_type,
            "direction": self.direction,
            "activated": self.activated,
            "exploded": self.is_exploded(),
            "explosion_cells": self.explosion_cells.copy(),
        }
        changes = {
            "entity_id": self.id
        }
        for key, value in current_state.items():
            if key not in previous_state or previous_state[key] != value:
                changes[key] = value
        self._state = current_state
        return WeaponUpdate(**changes)