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
    fps: float = 30.0 #TODO перенести этот параметр в settings проекта, это не настраиваемый пользователями параметр
    game_over_timeout: float = 5.0 #TODO перенести этот параметр в settings проекта, это не настраиваемый пользователями параметр
    
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
    
    # Режим игры
    game_mode: GameModeSettings = None
    
    def __post_init__(self):
        if self.game_mode is None:
            self.game_mode = GameModeSettings(mode_type=GameModeType.SINGLE_PLAYER) 