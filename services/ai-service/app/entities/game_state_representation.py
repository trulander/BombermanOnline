from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


class MapCellUpdate(BaseModel):
    x: int
    y: int
    type: int


class MapState(BaseModel):
    width: int
    height: int
    grid: List[List[int]]


class GamePlayerInfo(BaseModel):
    id: str
    user_id: str
    game_id: str
    x: float
    y: float
    lives: int
    bombs_left: int
    bomb_radius: int
    is_alive: bool
    speed: float
    max_bombs: int


class EnemyState(BaseModel):
    id: str
    x: float
    y: float
    lives: int
    is_alive: bool
    speed: float


class WeaponState(BaseModel):
    id: str
    x: float
    y: float
    weapon_type: str


class PowerUpState(BaseModel):
    id: str
    x: float
    y: float
    power_up_type: str


class GameStateRepresentation(BaseModel):
    game_id: str
    status: Literal["PENDING", "ACTIVE", "PAUSED", "FINISHED"]
    is_active: bool
    level: int
    players: Dict[str, GamePlayerInfo] = Field(default_factory=dict)
    enemies: Dict[str, EnemyState] = Field(default_factory=dict)
    weapons: Dict[str, WeaponState] = Field(default_factory=dict)
    power_ups: Dict[str, PowerUpState] = Field(default_factory=dict)


class GameUpdateEvent(BaseModel):
    game_id: str
    status: Literal["PENDING", "ACTIVE", "PAUSED", "FINISHED"]
    is_active: bool
    map_update: Optional[List[MapCellUpdate]] = None
    players_update: Optional[Dict[str, GamePlayerInfo]] = None
    enemies_update: Optional[Dict[str, EnemyState]] = None
    weapons_update: Optional[Dict[str, WeaponState]] = None
    power_ups_update: Optional[Dict[str, PowerUpState]] = None


class PlayerInput(BaseModel):
    up: bool = False
    down: bool = False
    left: bool = False
    right: bool = False
    weapon1: bool = False
    weapon2: bool = False
    action1: bool = False


class TrainingRequest(BaseModel):
    game_id: str
    player_id: str
    game_mode: str
    total_timesteps: int
    save_interval: int
    algorithm_name: str = "PPO"
    continue_training: bool = True
