from dataclasses import dataclass
from typing import Optional
from .game_mode import GameModeSettings, GameModeType


@dataclass
class GameSettings:
    """Настройки игры"""
    # Базовые настройки
    cell_size: int = 40
    default_map_width: int = 23
    default_map_height: int = 23
    
    # Настройки игроков
    max_players: int = 4
    player_start_lives: int = 3
    player_default_speed: float = 3.0
    player_invulnerable_time: float = 2.0
    
    # Настройки бомб
    bomb_timer: float = 2.0
    bomb_explosion_duration: float = 0.5
    default_bomb_power: int = 1
    default_max_bombs: int = 1
    
    # Настройки врагов
    enemy_destroy_animation_time: float = 0.5
    enemy_invulnerable_time: float = 2.0
    
    # Настройки очков
    block_destroy_score: int = 10
    enemy_destroy_score: int = 100
    powerup_collect_score: int = 25
    level_complete_score: int = 500
    
    # Вероятности появления
    powerup_drop_chance: float = 0.2
    enemy_powerup_drop_chance: float = 0.3
    
    # Настройки генерации карт
    enable_snake_walls: bool = False  # Генерация стен змейкой для некоторых режимов
    allow_enemies_near_players: bool = False  # Разрешить появление врагов рядом с игроками
    min_distance_from_players: int = 3  # Минимальное расстояние от игроков для врагов
    
    # Режим игры
    game_mode: GameModeSettings = None
    
    def __post_init__(self):
        if self.game_mode is None:
            self.game_mode = GameModeSettings(mode_type=GameModeType.SINGLE_PLAYER) 