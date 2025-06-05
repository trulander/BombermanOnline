from typing import Optional
from pydantic import BaseModel
from .game_mode import GameModeType
from ..models.team_models import TeamModeSettings


class GameSettings(BaseModel):
    """Настройки игры - плоский класс без иерархии"""
    # Базовые настройки
    cell_size: int = 40
    default_map_width: int = 23
    default_map_height: int = 23
    
    # Настройки игрока
    player_default_speed: float = 3.0
    player_invulnerable_time: float = 2.0

    # Настройки оружия
    bomb_timer: float = 2.0
    bomb_explosion_duration: float = 0.5
    default_bomb_power: int = 1
    default_max_bombs: int = 1
    bullet_speed: float = 5.0
    mine_timer: float = 5.0

    # Настройки врагов
    enemy_count_multiplier: float = 1.0
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
    enable_snake_walls: bool = False
    allow_enemies_near_players: bool = False
    min_distance_from_players: int = 1


   #Настраиваемые параметры во время создания игры
    game_id: str = None
    # Режим игры
    game_mode: GameModeType = GameModeType.CAMPAIGN
    # Настройки игроков и команд
    max_players: int = 4
    team_count: int = 1  # Для CAMPAIGN = 1, для FREE_FOR_ALL = количество игроков, для CAPTURE_THE_FLAG определяется картой
    player_start_lives: int = 3
    # Настройки врагов
    enable_enemies: bool = True
    # Настройки карт
    map_chain_id: Optional[str] = None
    map_template_id: Optional[str] = None
    # Игровые настройки
    respawn_enabled: bool = False
    friendly_fire: bool = False
    time_limit: Optional[int] = 300  # в секундах
    score_limit: Optional[int] = 10
    rounds_count: Optional[int] = 15

    @property
    def team_mode_settings(self) -> TeamModeSettings:
        match self.game_mode:
            case GameModeType.FREE_FOR_ALL:
                return TeamModeSettings(
                    game_mode=GameModeType.FREE_FOR_ALL,
                    default_team_count=0,  # Каждый игрок в своей команде
                    max_team_count=8,
                    min_players_per_team=1,
                    max_players_per_team=1,
                    auto_distribute_players=True,
                    allow_uneven_teams=True,
                    default_team_names=[]  # Имена генерируются автоматически
                )
            case GameModeType.CAPTURE_THE_FLAG:
                return TeamModeSettings(
                    game_mode=GameModeType.CAPTURE_THE_FLAG,
                    default_team_count=2,
                    max_team_count=4,
                    min_players_per_team=1,
                    max_players_per_team=4,
                    auto_distribute_players=True,
                    allow_uneven_teams=False,
                    default_team_names=["Red Team", "Blue Team", "Green Team", "Yellow Team"]
                )
            case _: # значение по умолчанию для GameModeType.CAMPAIGN
                return TeamModeSettings(
                    game_mode = GameModeType.CAMPAIGN,
                    default_team_count=1,
                    max_team_count=1,
                    min_players_per_team=1,
                    max_players_per_team=8,
                    auto_distribute_players=True,
                    allow_uneven_teams=True,
                    default_team_names=["Heroes"]
                )

