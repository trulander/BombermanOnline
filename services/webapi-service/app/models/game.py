from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any

from ..entities.game_mode import GameModeType


class GameCreateSettings(BaseModel):
    # game_id: str = str(uuid4())
    # Режим игры
    game_mode: GameModeType = GameModeType.CAMPAIGN
    # Настройки игроков и команд
    max_players: int = 4
    player_start_lives: int = 3

    # Настройки врагов
    enable_enemies: bool = True

    # Настройки карт
    map_chain_id: str | None = None
    map_template_id: str | None = None

    # Игровые настройки
    respawn_enabled: bool = False
    friendly_fire: bool = False
    time_limit: int | None = 300  # в секундах
    score_limit: int | None = 10
    rounds_count: int | None = 15

class JoinGameRequest(BaseModel):
    """Модель для присоединения к игре"""
    game_id: str = Field(..., description="Идентификатор игры")

class JoinGameResponse(BaseModel):
    """Модель ответа при присоединении к игре"""
    game_id: str = Field(..., description="Идентификатор игры")
    player_id: str = Field(..., description="Идентификатор игрока")
    success: bool = Field(..., description="Успешно или нет")
    message: str | None = Field(None, description="Сообщение об ошибке")

class PlayerInput(BaseModel):
    """Модель ввода игрока"""
    up: bool = Field(False, description="Движение вверх")
    down: bool = Field(False, description="Движение вниз")
    left: bool = Field(False, description="Движение влево")
    right: bool = Field(False, description="Движение вправо")

class InputRequest(BaseModel):
    """Модель запроса на отправку ввода"""
    game_id: str = Field(..., description="Идентификатор игры")
    inputs: PlayerInput = Field(..., description="Ввод игрока")

class PlaceWeaponRequest(BaseModel):
    """Модель запроса на применение оружия"""
    game_id: str = Field(..., description="Идентификатор игры")
    weapon_type: str = Field("bomb", description="Тип оружия (bomb, bullet, mine)")

class GameState(BaseModel):
    """Модель состояния игры"""
    players: Dict[str, Any] = Field(default_factory=dict, description="Информация об игроках")
    enemies: List[Any] = Field(default_factory=list, description="Информация о врагах")
    bombs: List[Any] = Field(default_factory=list, description="Информация о бомбах")
    powerUps: List[Any] = Field(default_factory=list, description="Информация о бонусах")
    map: Dict[str, Any] = Field(default_factory=dict, description="Информация о карте")
    score: int = Field(0, description="Текущий счет")
    level: int = Field(1, description="Текущий уровень")
    gameOver: bool = Field(False, description="Игра окончена") 