from typing import List, Optional, Dict, Tuple, Any, TYPE_CHECKING
from datetime import datetime
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, JSON, Boolean, DateTime, Float
from sqlalchemy.ext.declarative import declarative_base

from app.entities import EnemyType, PowerUpType, CellType
from app.entities.game_status import GameStatus
from app.entities.player import UnitType
from app.entities.weapon import WeaponType

if TYPE_CHECKING:
    from app.models.game_models import GameTeamInfo

Base = declarative_base()

# SQLAlchemy модели для базы данных
class MapTemplateORM(Base):
    __tablename__ = "map_templates"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    width = Column(Integer, nullable=False)
    height = Column(Integer, nullable=False)
    grid_data = Column(JSON, nullable=False)
    difficulty = Column(Integer, nullable=False, default=1)
    max_players = Column(Integer, nullable=False, default=4)
    min_players = Column(Integer, nullable=False, default=1)
    estimated_play_time = Column(Integer, nullable=False, default=300)
    tags = Column(JSON)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


class MapGroupORM(Base):
    __tablename__ = "map_groups"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    map_ids = Column(JSON, nullable=False)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


class MapChainORM(Base):
    __tablename__ = "map_chains"
    
    id = Column(String, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    map_ids = Column(JSON, nullable=False)
    difficulty_progression = Column(Float, nullable=False, default=1.0)
    created_by = Column(String(255), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, nullable=False, default=True)


# Pydantic модели для API
class MapTemplateBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    width: int = Field(..., ge=5, le=50)
    height: int = Field(..., ge=5, le=50)
    grid_data: List[List[int]] = Field(..., description="2D array representing the map grid")
    difficulty: int = Field(1, ge=1, le=10)
    max_players: int = Field(4, ge=1, le=8)
    min_players: int = Field(1, ge=1)
    estimated_play_time: int = Field(300, ge=60, description="Estimated play time in seconds")
    tags: List[str] = Field(default_factory=list)


class MapTemplateCreate(MapTemplateBase):
    pass


class MapTemplateUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    width: Optional[int] = Field(None, ge=5, le=50)
    height: Optional[int] = Field(None, ge=5, le=50)
    grid_data: Optional[List[List[int]]] = None
    difficulty: Optional[int] = Field(None, ge=1, le=10)
    max_players: Optional[int] = Field(None, ge=1, le=8)
    min_players: Optional[int] = Field(None, ge=1)
    estimated_play_time: Optional[int] = Field(None, ge=60)
    tags: Optional[List[str]] = None


class MapTemplate(MapTemplateBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: MapTemplateORM):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            width=obj.width,
            height=obj.height,
            grid_data=obj.grid_data,
            difficulty=obj.difficulty,
            max_players=obj.max_players,
            min_players=obj.min_players,
            estimated_play_time=obj.estimated_play_time,
            tags=obj.tags or [],
            created_by=obj.created_by,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            is_active=obj.is_active
        )


class MapGroupBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    map_ids: List[str] = Field(min_length=1)


class MapGroupCreate(MapGroupBase):
    pass


class MapGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    map_ids: Optional[List[str]] = Field(min_length=1)


class MapGroup(MapGroupBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: MapGroupORM):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            map_ids=obj.map_ids or [],
            created_by=obj.created_by,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            is_active=obj.is_active
        )


class MapChainBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    map_ids: List[str] = Field(min_length=1)
    difficulty_progression: float = Field(1.0, ge=0.1, le=5.0)


class MapChainCreate(MapChainBase):
    pass


class MapChainUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    map_ids: Optional[List[str]] = Field(min_length=1)
    difficulty_progression: Optional[float] = Field(None, ge=0.1, le=5.0)


class MapChain(MapChainBase):
    id: str
    created_by: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    class Config:
        from_attributes = True

    @classmethod
    def from_orm(cls, obj: MapChainORM):
        return cls(
            id=obj.id,
            name=obj.name,
            description=obj.description,
            map_ids=obj.map_ids or [],
            difficulty_progression=obj.difficulty_progression,
            created_by=obj.created_by,
            created_at=obj.created_at,
            updated_at=obj.updated_at,
            is_active=obj.is_active
        )


# Фильтры для поиска
class MapTemplateFilter(BaseModel):
    name: Optional[str] = None
    difficulty_min: Optional[int] = Field(None, ge=1, le=10)
    difficulty_max: Optional[int] = Field(None, ge=1, le=10)
    max_players_min: Optional[int] = Field(None, ge=1, le=8)
    max_players_max: Optional[int] = Field(None, ge=1, le=8)
    tags: Optional[List[str]] = None
    created_by: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MapGroupFilter(BaseModel):
    name: Optional[str] = None
    created_by: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class MapChainFilter(BaseModel):
    name: Optional[str] = None
    created_by: Optional[str] = None
    is_active: Optional[bool] = True
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class PlayerState(BaseModel):
    name: str | None = None
    team_id: str
    player_id: str
    x: float
    y: float
    lives: int
    primary_weapon: WeaponType
    primary_weapon_max_count: int
    primary_weapon_power: int
    secondary_weapon: Optional[WeaponType] = None
    secondary_weapon_max_count: Optional[int] = None
    secondary_weapon_power: Optional[int] = None
    invulnerable: bool
    color: str
    unit_type: UnitType


class EnemyState(BaseModel):
    x: float
    y: float
    type: EnemyType
    lives: int
    invulnerable: bool
    destroyed: bool


class WeaponState(BaseModel):
    x: float
    y: float
    type: WeaponType
    direction: Optional[tuple[float, float]] = None
    activated: bool
    exploded: bool
    explosion_cells: list[tuple[int, int]]
    owner_id: str


class PowerUpState(BaseModel):
    x: float
    y: float
    type: PowerUpType


class MapData(BaseModel):
    grid: list | None
    width: int
    height: int


class MapState(BaseModel):
    players: dict[str, PlayerState]
    enemies: list[EnemyState]
    weapons: list[WeaponState]
    power_ups: list[PowerUpState]
    map: MapData
    level: int
    error: Optional[bool] = None
    is_active: Optional[bool] = None
    status: GameStatus = None
    teams: Optional[dict[str, "GameTeamInfo"]] = None


class MapUpdate(BaseModel):
    x: int
    y: int
    type: CellType