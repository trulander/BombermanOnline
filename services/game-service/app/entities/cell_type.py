from enum import IntEnum

class CellType(IntEnum):
    """Типы ячеек на карте"""
    EMPTY = 0
    SOLID_WALL = 1
    BREAKABLE_BLOCK = 2
    PLAYER_SPAWN = 3
    ENEMY_SPAWN = 4