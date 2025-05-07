from uuid import uuid4
from pydantic import BaseModel, Field, field_validator
from typing import Dict, List, Any

class GameCreate(BaseModel):
    """Модель для создания новой игры"""
    pass

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

class PlaceBombRequest(BaseModel):
    """Модель запроса на установку бомбы"""
    game_id: str = Field(..., description="Идентификатор игры")

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