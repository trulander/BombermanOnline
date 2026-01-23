from fastapi import APIRouter, Depends, HTTPException, status
import logging

from ...models.game import JoinGameRequest, JoinGameResponse, InputRequest, PlaceWeaponRequest, \
    GameCreateSettings, GameListItem, GameFilter
from ...services.game_service import GameService
from ...dependencies import get_game_service, get_game_aggregator_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=list[GameListItem])
async def get_games(
    filter: GameFilter = Depends(GameFilter),
    aggregator_service = Depends(get_game_aggregator_service),
):
    """
    Получить список всех игр со всех инстансов game-service
    """
    try:
        all_games = await aggregator_service.get_all_games(game_filter=filter)
        
        all_games_list = [GameListItem(**game) for game in all_games]
        
        total_games = all_games_list[filter.offset:filter.offset + filter.limit]
        logger.info(f"Returning {len(total_games)} games (filtered from {len(all_games_list)} total)")
        return total_games
    except Exception as e:
        logger.error(f"Error getting games list: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting games list: {str(e)}"
        )

@router.post("/", response_model=dict)
async def create_game(
        init_params: GameCreateSettings,
        game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Создать новую игру
    """
    try:
        logger.info("Handling request to create a new game")
        logger.debug(f"payload: {init_params}")
        result = await game_service.create_game(init_params=init_params)
        
        if not result.get("success"):
            logger.warning(f"Failed to create game: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("message", "Failed to create game")
            )
        
        logger.info(f"Game created successfully with ID: {result.get('game_id')}")
        return result
    except HTTPException:
        # Re-raise HTTPException to maintain FastAPI's error handling
        raise
    except Exception as e:
        logger.error(f"Unexpected error creating game: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )
