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
    explosion_cells: NotRequired[set[tuple[int, int]]]
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

        # Explosion cells will be populated when the bomb explodes (or pre-filled in Bomb/Mine __init__)
        self.explosion_cells_grid: set[tuple[int, int]] = set()
        # Blocks destroyed by this explosion (filled in activate() when iterating explosion_cells_grid)
        self.destroyed_blocks: list[tuple[int, int]] = []

        logger.debug(f"Weapon created: type={self.weapon_type.value}, position=({x}, {y}), owner={owner_id}")


    def activate(self, **kwargs) -> bool:
        """Activate weapon (explosion, shot, etc.). Explosion geometry must already be in explosion_cells_grid
        (filled by _fill_explosion_area_geometry in Bomb/Mine __init__, or by subclass before super().activate()).
        Destroys breakable blocks for each cell in explosion_cells_grid, then marks activated and runs handler.
        """
        if not self.activated:
            handle_weapon_explosion: Callable = kwargs.get('handle_weapon_explosion')
            # Destroy breakable blocks for each cell in pre-filled explosion area (no geometry calc here)
            for cell_x, cell_y in self.explosion_cells_grid:
                if self.map.is_breakable_block(cell_x, cell_y):
                    if self.map.destroy_block(cell_x, cell_y):
                        self.destroyed_blocks.append((cell_x, cell_y))
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

    
    def get_damage_area(self) -> set[tuple[int, int]]:
        """Return explosion damage area (grid cells). Always returns explosion_cells_grid so collision
        and 'entity in blast zone' checks work even before activation (e.g. for placed bombs/mines).
        """
        return self.explosion_cells_grid


    def get_destroyed_blocks(self) -> list[tuple[int, int]]:
        if self.activated:
            return self.destroyed_blocks
        return []


    def _fill_explosion_area_geometry(self) -> None:
        grid_x: int = int(self.x / self.settings.cell_size)
        grid_y: int = int(self.y / self.settings.cell_size)

        self.explosion_cells_grid.add((grid_x, grid_y))

        directions: list[tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        for dx, dy in directions:
            for i in range(1, self.power + 1):
                check_x: int = grid_x + (dx * i)
                check_y: int = grid_y + (dy * i)

                if self.map.is_wall(check_x, check_y):
                    break

                self.explosion_cells_grid.add((check_x, check_y))

                # Include breakable cell in zone but stop the ray (no destroy_block here)
                if self.map.is_breakable_block(check_x, check_y):
                    break


    def is_entity_in_blast_zone(self, entity_x: float, entity_y: float) -> bool:
        """Check if entity at (entity_x, entity_y) is inside this weapon's blast zone (grid cell)."""
        cell_size: int = self.settings.cell_size
        gx: int = round(entity_x / cell_size)
        gy: int = round(entity_y / cell_size)
        return (gx, gy) in self.explosion_cells_grid


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
            "explosion_cells": self.explosion_cells_grid.copy(),
            "owner_id": self.owner_id
        }
        changes = {
            "entity_id": self.id
        }
        for key, value in current_state.items():
            if key not in previous_state or previous_state[key] != value:
                changes[key] = value
        self._state = current_state
        return WeaponUpdate(**changes)