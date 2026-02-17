from datetime import datetime
from typing import Optional, List
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from app.entities import EnemyType
from app.entities.enemy import EnemyUpdate
from app.entities.game_status import GameStatus
from app.entities.game_mode import GameModeType
from app.entities.player import UnitType, PlayerUpdate
from app.entities.power_up import PowerUpUpdate
from app.entities.weapon import WeaponUpdate
from app.models.map_models import MapUpdate, PlayerState
from app.models.team_models import TeamModeSettings


class GameUpdateEvent(BaseModel):
    status: GameStatus
    is_active: bool
    error: bool = False
    message: Optional[str] = None
    map_update: list[MapUpdate] = None
    players_update: dict[str, PlayerUpdate] = None
    enemies_update: dict[str, EnemyUpdate] = None
    weapons_update: dict[str, WeaponUpdate] = None
    power_ups_update: dict[str, PowerUpUpdate] = None
    #TODO Добавить teams
    game_id: str = None
    # Оставшееся время обратного отсчёта (None = таймер не активен)
    time_remaining: Optional[float] = None


# class GamePlayerInfo(BaseModel):
#     """Информация об игроке в игре"""
#     id: str
#     name: str | None = None
#     unit_type: UnitType
#     team_id: Optional[str] = None
#     lives: int
#     x: float
#     y: float
#     color: str
#     invulnerable: bool = False


class GameTeamInfo(BaseModel):
    """Информация о команде в игре"""
    id: str
    name: str
    score: int
    player_ids: List[str]
    player_count: int


class GameInfo(BaseModel):
    """Полная информация об игре"""
    game_id: str
    status: GameStatus
    game_mode: GameModeType
    max_players: int
    current_players_count: int
    team_count: int
    level: int
    game_over: bool
    players: List[PlayerState]
    teams: List[GameTeamInfo]
    settings: dict  # GameSettings в виде словаря
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class GameListItem(BaseModel):
    """Краткая информация об игре для списка"""
    game_id: str
    status: GameStatus
    game_mode: GameModeType
    current_players_count: int
    max_players: int
    level: int
    created_at: Optional[datetime] = None


class GameFilter(BaseModel):
    """Фильтры для поиска игр"""
    status: Optional[GameStatus] = None
    game_mode: Optional[GameModeType] = None
    has_free_slots: Optional[bool] = None
    min_players: Optional[int] = Field(None, ge=0, le=8)
    max_players: Optional[int] = Field(None, ge=1, le=8)
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class GameStatusUpdate(BaseModel):
    """Модель для изменения статуса игры"""
    action: str = Field(..., pattern="^(start|pause|resume)$")


class PlayerAction(BaseModel):
    """Модель для действий с игроками"""
    player_id: str
    unit_type: Optional[UnitType] = UnitType.BOMBERMAN,
    ai_player: bool = False


class GameCreateResponse(BaseModel):
    """Ответ при создании игры"""
    success: bool
    game_id: Optional[str] = None
    message: Optional[str] = None


class StandardResponse(BaseModel):
    """Стандартный ответ API"""
    success: bool
    message: Optional[str] = None
    data: Optional[dict] = None


class GameSettingsUpdate(BaseModel):
    """Модель для обновления настроек игры"""
    # Настройки игроков и команд
    max_players: int = 4
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


class GameCreateSettings(GameSettingsUpdate):
    # Режим игры
    game_mode: GameModeType = GameModeType.CAMPAIGN


class GameSettings(BaseModel):
    """Настройки игры - плоский класс без иерархии"""
    # Базовые настройки
    cell_size: int = 40
    default_map_width: int = 23
    default_map_height: int = 23
    destroy_animation_time: float = 0.5
    destroy_inactive_time: float = 300

    # Настройки игрока
    player_default_speed: float = 3.0
    player_invulnerable_time: float = 2.0
    player_max_speed: float = 6.0
    player_max_lives: int = 10
    destroy_disconnected_time: float = 25

    # Настройки оружия
    bomb_timer: float = 2.0 #таймер для автоматического взрыва установленной бомбы
    bomb_explosion_duration: float = 0.5# таймер продолжительности взрыва
    default_bomb_power: int = 1
    max_bomb_power: int = 10 #TODO имплементировать лимиты на увеличение максимальной мощности бомб у юнита
    max_bomb_count: int = 10 #TODO имплементировать лимиты на увеличение максимального количества бомб у юнита
    default_count_bombs: int = 1
    bullet_speed: float = 5.0
    mine_timer: float = 5.0

    # Настройки врагов
    enemy_count_multiplier: float = 1.0
    enemy_invulnerable_time: float = 2.0
    enemy_ai_controlled: bool = True

    # Настройки очков
    block_destroy_score: int = 30
    enemy_destroy_score: int = 500
    player_destroy_score: int = 500
    powerup_collect_score: int = 30
    level_complete_score: int = 500

    # Вероятности появления
    powerup_drop_chance: float = 0.2
    enemy_powerup_drop_chance: float = 0.3

    # Настройки генерации карт
    enable_snake_walls: bool = False
    allow_enemies_near_players: bool = True
    min_distance_from_players: int = 1


    #Настраиваемые параметры во время создания игры
    game_id: str = None
    # Режим игры
    game_mode: GameModeType = GameModeType.CAMPAIGN
    # Настройки игроков и команд
    max_players: int = 4
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

    @computed_field(return_type=TeamModeSettings)
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
