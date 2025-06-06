from pydantic import BaseModel
from app.entities import GameModeType


# Pydantic модели для API
class GameCreateSettings(BaseModel):
    game_id: str = None
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