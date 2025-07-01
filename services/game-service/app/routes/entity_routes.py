from fastapi import APIRouter, Depends
import logging
from typing import Any

from app.auth import get_current_user


from app.entities.bomb import Bomb
from app.entities.bomberman import Bomberman
from app.entities.bullet import Bullet
from app.entities.cell_type import CellType
from app.entities.enemy import EnemyType, Enemy
from app.entities.game_mode import GameModeType
from app.entities.game_status import GameStatus
from app.entities.mine import Mine
from app.entities.power_up import PowerUpType, PowerUp
from app.entities.tank import Tank
from app.entities.entity import Entity # Base Entity
from app.entities.player import Player # Base Player
from app.entities.weapon import Weapon # Base Weapon
from app.models.game_models import GameSettings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/entities", tags=["entities"])



@router.get("/info", response_model=dict[str, Any])
async def get_entities_info(
    #current_user: dict = Depends(get_current_user)
) -> dict[str, Any]:
    """Get information about available entities and their types."""
    info: dict[str, Any] = {}
    cell_size: int = GameSettings().cell_size
    # Helper to get dimensions for entities with scale_size
    def get_dimensions(entity_class: type[Entity]) -> dict[str, float]:
        if hasattr(entity_class, 'scale_size'):
            scale = entity_class.scale_size
            return {
                "width": cell_size * scale,
                "height": cell_size * scale
            }
        return {"width": 0.0, "height": 0.0}

    # CellType Enum
    info["cell_types"] = {
        member.name: member.value for member in CellType
    }

    # GameModeType Enum
    info["game_modes"] = {
        member.name: member.value for member in GameModeType
    }

    # GameStatus Enum
    info["game_statuses"] = {
        member.name: member.value for member in GameStatus
    }

    # EnemyType Enum with dimensions
    enemy_dimensions = get_dimensions(Enemy)
    info["enemy_types"] = {
        member.name: {
            "value": member.value,
            "width": enemy_dimensions["width"],
            "height": enemy_dimensions["height"]
        } for member in EnemyType
    }

    # PowerUpType Enum with dimensions
    power_up_dimensions = get_dimensions(PowerUp)
    info["power_up_types"] = {
        member.name: {
            "value": member.value,
            "width": power_up_dimensions["width"],
            "height": power_up_dimensions["height"]
        } for member in PowerUpType
    }

    # Player types (Bomberman, Tank) with dimensions
    info["player_units"] = {
        "BOMBERMAN": {
            "name": "Bomberman",
            **get_dimensions(Bomberman)
        },
        "TANK": {
            "name": "Tank",
            **get_dimensions(Tank)
        }
    }

    # Weapon types (Bomb, Bullet, Mine) with dimensions
    info["weapon_types"] = {
        "BOMB": {
            "name": "Bomb",
            **get_dimensions(Bomb)
        },
        "BULLET": {
            "name": "Bullet",
            **get_dimensions(Bullet)
        },
        "MINE": {
            "name": "Mine",
            **get_dimensions(Mine)
        }
    }
    
    logger.info("Entities info requested")
    return info 