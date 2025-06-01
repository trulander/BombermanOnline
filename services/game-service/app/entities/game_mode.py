from enum import Enum
from dataclasses import dataclass
from typing import Optional


class GameModeType(Enum):
    """Типы игровых режимов"""
    SINGLE_PLAYER = "single_player"       # Прохождение одним игроком
    DEATHMATCH = "deathmatch"             # Все против всех
    COOPERATIVE = "cooperative"           # Кооперативное прохождение
    TEAM_CAPTURE_FLAG = "team_capture_flag"  # Командная игра с флагами
    CUSTOM = "custom"                     # Настраиваемая игра


@dataclass
class GameModeSettings:
    """Настройки игрового режима"""
    mode_type: GameModeType
    max_players: int = 4
    enable_enemies: bool = True
    enemy_count_multiplier: float = 1.0
    map_chain_id: Optional[str] = None
    map_group_id: Optional[str] = None
    rounds_count: Optional[int] = None
    team_count: int = 2
    respawn_enabled: bool = False
    friendly_fire: bool = False
    time_limit: Optional[int] = None  # в секундах
    score_limit: Optional[int] = None 