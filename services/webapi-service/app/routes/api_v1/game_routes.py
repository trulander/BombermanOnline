from fastapi import APIRouter, Depends, HTTPException, status
import logging

from ...models.game import GameCreate, JoinGameRequest, JoinGameResponse, InputRequest, PlaceBombRequest
from ...services.game_service import GameService
from ...dependencies import get_game_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/", response_model=dict)
async def create_game(
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Создать новую игру
    """
    try:
        logger.info("Handling request to create a new game")
        result = await game_service.create_game()
        
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

@router.post("/join", response_model=JoinGameResponse)
async def join_game(
    join_request: JoinGameRequest,
    game_service: GameService = Depends(get_game_service)
) -> JoinGameResponse:
    """
    Присоединиться к существующей игре
    """
    try:
        logger.info(f"Handling request to join game {join_request.game_id}")
        result = await game_service.join_game(join_request.game_id)
        
        if not result.success:
            logger.warning(f"Failed to join game {join_request.game_id}: {result.message}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.message or "Failed to join game"
            )
        
        logger.info(f"Player {result.player_id} joined game {result.game_id} successfully")
        return result
    except HTTPException:
        # Re-raise HTTPException to maintain FastAPI's error handling
        raise
    except Exception as e:
        logger.error(f"Unexpected error joining game {join_request.game_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.post("/input")
async def send_input(
    input_request: InputRequest,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Отправить ввод игрока
    
    Эта функция используется для отправки управления в игру.
    """
    try:
        # В реальном приложении здесь нужно было бы получить player_id из JWT токена
        # или другого метода аутентификации
        player_id = "player123"  # Заглушка, обычно получаем из токена
        
        logger.debug(f"Sending input for player {player_id} in game {input_request.game_id}: {input_request.inputs}")
        
        await game_service.send_input(
            game_id=input_request.game_id,
            player_id=player_id,
            inputs=dict(input_request.inputs)
        )
        
        logger.debug(f"Input sent successfully for player {player_id} in game {input_request.game_id}")
        return {"success": True}
    except Exception as e:
        logger.error(f"Error sending input for player in game {input_request.game_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred while sending input"
        )

@router.post("/place-bomb")
async def place_bomb(
    request: PlaceBombRequest,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Установить бомбу
    
    Эта функция используется для установки бомбы в игре.
    """
    try:
        # В реальном приложении здесь нужно было бы получить player_id из JWT токена
        player_id = "player123"  # Заглушка, обычно получаем из токена
        
        logger.debug(f"Player {player_id} requesting to place bomb in game {request.game_id}")
        
        result = await game_service.place_bomb(
            game_id=request.game_id,
            player_id=player_id
        )
        
        if not result.get("success"):
            logger.warning(f"Failed to place bomb in game {request.game_id}: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.get("message", "Failed to place bomb")
            )
        
        logger.debug(f"Bomb placed successfully by player {player_id} in game {request.game_id}")
        return result
    except HTTPException:
        # Re-raise HTTPException to maintain FastAPI's error handling
        raise
    except Exception as e:
        logger.error(f"Unexpected error placing bomb in game {request.game_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )

@router.get("/{game_id}/state")
async def get_game_state(
    game_id: str,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Получить состояние игры
    
    Эта функция используется для получения текущего состояния игры.
    """
    try:
        logger.debug(f"Getting state for game {game_id}")
        
        result = await game_service.get_game_state(game_id)
        
        if not result.get("success"):
            logger.warning(f"Failed to get state for game {game_id}: {result.get('message')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=result.get("message", "Game not found")
            )
        
        logger.debug(f"Successfully retrieved state for game {game_id}")
        return result
    except HTTPException:
        # Re-raise HTTPException to maintain FastAPI's error handling
        raise
    except Exception as e:
        logger.error(f"Unexpected error getting state for game {game_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred"
        )