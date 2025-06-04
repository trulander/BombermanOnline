from typing import List, Optional
from pydantic import BaseModel, Field


class TeamBase(BaseModel):
    """Базовая модель команды."""
    name: str = Field(..., min_length=1, max_length=50, description="Название команды")


class TeamCreate(TeamBase):
    """Модель для создания команды."""
    pass


class TeamUpdate(BaseModel):
    """Модель для обновления команды."""
    name: Optional[str] = Field(None, min_length=1, max_length=50, description="Новое название команды")


class Team(TeamBase):
    """Модель команды для API ответов."""
    id: str = Field(..., description="Уникальный идентификатор команды")
    score: int = Field(default=0, description="Очки команды")
    player_ids: List[str] = Field(default_factory=list, description="Список ID игроков в команде")
    player_count: int = Field(default=0, description="Количество игроков в команде")

    model_config = {"from_attributes": True}


class PlayerTeamAction(BaseModel):
    """Модель для добавления/удаления игрока из команды."""
    player_id: str = Field(..., description="ID игрока")


class TeamDistributionRequest(BaseModel):
    """Модель для автоматического распределения игроков по командам."""
    redistribute_existing: bool = Field(default=False, description="Перераспределить существующих игроков")


class TeamModeSettings(BaseModel):
    """Настройки команд для конкретного игрового режима."""
    default_team_count: int
    max_team_count: int
    min_players_per_team: int
    max_players_per_team: int
    auto_distribute_players: bool
    allow_uneven_teams: bool
    default_team_names: List[str]
