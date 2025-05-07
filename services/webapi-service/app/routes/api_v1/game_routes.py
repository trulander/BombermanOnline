from fastapi import APIRouter, Depends, HTTPException, status

from ...models.game import GameCreate, JoinGameRequest, JoinGameResponse, InputRequest, PlaceBombRequest
from ...services.game_service import GameService
from ...dependencies import get_game_service

router = APIRouter()

@router.post("/", response_model=dict)
async def create_game(
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Создать новую игру
    """
    result = await game_service.create_game()
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "Failed to create game")
        )
    return result

@router.post("/join", response_model=JoinGameResponse)
async def join_game(
    join_request: JoinGameRequest,
    game_service: GameService = Depends(get_game_service)
) -> JoinGameResponse:
    """
    Присоединиться к существующей игре
    """
    result = await game_service.join_game(join_request.game_id)
    if not result.success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.message or "Failed to join game"
        )
    return result

@router.post("/input")
async def send_input(
    input_request: InputRequest,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Отправить ввод игрока
    
    Эта функция используется для отправки управления в игру.
    """
    # В реальном приложении здесь нужно было бы получить player_id из JWT токена
    # или другого метода аутентификации
    player_id = "player123"  # Заглушка, обычно получаем из токена
    
    await game_service.send_input(
        game_id=input_request.game_id,
        player_id=player_id,
        inputs=dict(input_request.inputs)
    )
    
    return {"success": True}

@router.post("/place-bomb")
async def place_bomb(
    request: PlaceBombRequest,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Установить бомбу
    
    Эта функция используется для установки бомбы в игре.
    """
    # В реальном приложении здесь нужно было бы получить player_id из JWT токена
    player_id = "player123"  # Заглушка, обычно получаем из токена
    
    result = await game_service.place_bomb(
        game_id=request.game_id,
        player_id=player_id
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("message", "Failed to place bomb")
        )
    
    return result

@router.get("/{game_id}/state")
async def get_game_state(
    game_id: str,
    game_service: GameService = Depends(get_game_service)
) -> dict:
    """
    Получить состояние игры
    
    Эта функция используется для получения текущего состояния игры.
    """
    result = await game_service.get_game_state(game_id)
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("message", "Game not found")
        )
    
    return result 