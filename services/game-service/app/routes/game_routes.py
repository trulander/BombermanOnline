import logging
import uuid
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
from fastapi import APIRouter, HTTPException, Depends, Query
from app.auth import get_current_user
from app.dependenties import game_coordinator
from app.models.game_models import (
    GameInfo, GameListItem, GameFilter, GameSettingsUpdate,
    GameStatusUpdate, PlayerAction, GameCreateResponse, StandardResponse,
    GameTeamInfo, GameCreateSettings
)

from app.entities.game_status import GameStatus
from app.entities.game_mode import GameModeType
from app.entities.player import UnitType
from app.models.map_models import PlayerState

if TYPE_CHECKING:
    from app.coordinators.game_coordinator import GameCoordinator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/games", tags=["games"])

def get_game_coordinator() -> "GameCoordinator":
    """Получить экземпляр GameCoordinator"""
    if game_coordinator is None:
        raise HTTPException(status_code=500, detail="Game coordinator not initialized")
    return game_coordinator


@router.get("/", response_model=List[GameListItem])
async def get_games(
    filter: GameFilter = Depends(GameFilter),
    # current_user: dict = Depends(get_current_user)
):
    """Получить список игр с фильтрацией"""
    coordinator = get_game_coordinator()
    
    # Получаем все активные игры
    all_games = []
    logger.info(f"coordinator.games: {coordinator.games}")
    for game_id, game_service in coordinator.games.items():
        try:
            game_state = game_service.get_state()
            logger.info(f"game {game_id} state: {game_state}")
            # Применяем фильтры
            if filter.status and game_service.status != filter.status:
                continue
                
            if filter.game_mode and game_service.settings.game_mode != filter.game_mode:
                continue
                
            current_players = len(game_state.players)
            max_game_players = game_service.settings.max_players
            
            if filter.has_free_slots and current_players >= max_game_players:
                continue
                
            if filter.min_players and current_players < filter.min_players:
                continue
                
            if filter.max_players and current_players > filter.max_players:
                continue
            
            game_item = GameListItem(
                game_id=game_id,
                status=game_service.status,
                game_mode=game_service.settings.game_mode,
                current_players_count=current_players,
                max_players=max_game_players,
                level=game_state.level,
                created_at=datetime.utcnow()  # TODO: добавить created_at в GameService
            )
            all_games.append(game_item)
            
        except Exception as e:
            # Пропускаем игры с ошибками
            logger.error(f"Exception: {e}")
            continue
    logger.info(f"all_games: {all_games}")
    # Применяем пагинацию
    total_games = all_games[filter.offset:filter.offset + filter.limit]
    return total_games


@router.get("/{game_id}", response_model=GameInfo)
async def get_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Получить подробную информацию об игре"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        game_state = game_service.get_state()
        
        # Формируем информацию об игроках
        players_info = []
        for player_id, player_state_data in game_state.players.items():

            if not player_state_data:
                logger.warning(f"Player entity {player_id} not found in game_service.players for game {game_id}")
                continue # Пропускаем этого игрока, если не найден

            # player_info = PlayerState(
            #     player_id=player_id,
            #     name=player_state_data.name, # Получаем name из Player entity
            #     unit_type=player_state_data.unit_type,
            #     team_id=player_state_data.team_id, # Получаем team_id из Player entity
            #     lives=player_state_data.lives,
            #     x=player_state_data.x,
            #     y=player_state_data.y,
            #     color=player_state_data.color,
            #     invulnerable=player_state_data.invulnerable,
            #     primary_weapon=p
            # )
            players_info.append(player_state_data)
        
        # Формируем информацию о командах
        teams_info = []
        teams_state = game_service.team_service.get_teams_state()
        for team_data in teams_state.values():
            team_info = GameTeamInfo(
                id=team_data['id'],
                name=team_data['name'],
                score=team_data['score'],
                player_ids=team_data['player_ids'],
                player_count=team_data['player_count']
            )
            teams_info.append(team_info)
        
        # Конвертируем GameSettings в словарь
        settings_dict = game_service.settings.model_dump()
        
        game_info = GameInfo(
            game_id=game_id,
            status=game_service.status,
            game_mode=game_service.settings.game_mode,
            max_players=game_service.settings.max_players,
            current_players_count=len(players_info),
            team_count=len(teams_info),
            level=game_state.level,
            game_over=game_service.game_mode.game_over,
            players=players_info,
            teams=teams_info,
            settings=settings_dict,
            created_at=datetime.utcnow(),  # TODO: добавить created_at в GameService
            updated_at=datetime.utcnow()   # TODO: добавить updated_at в GameService
        )
        
        return game_info
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting game info: {str(e)}")


#the endpoint is deprecated, need to use another andpoint in the webapi-service co create game
# @router.post("/", response_model=GameCreateResponse)
# async def create_game(
#     game_settings: GameCreateSettings,
#     # current_user: dict = Depends(get_current_user)
# ):
#     """Создать новую игру"""
#     coordinator = get_game_coordinator()

#     try:
#         # Вызываем метод создания игры через GameCoordinator
#         new_game_settings = game_settings.model_dump()

#         new_game_settings['game_id'] = str(uuid.uuid4())
#         result = await coordinator.game_create(new_game_settings=new_game_settings)

#         if result.get('success'):
#             return GameCreateResponse(
#                 success=True,
#                 game_id=result.get('game_id'),
#                 message="Game created successfully"
#             )
#         else:
#             return GameCreateResponse(
#                 success=False,
#                 message=result.get('message', 'Failed to create game')
#             )

#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error creating game: {str(e)}")


@router.put("/{game_id}/settings", response_model=StandardResponse)
async def update_game_settings(
    game_id: str,
    settings_update: GameSettingsUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Обновить настройки игры (только в статусе PENDING)"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail="Game settings can only be modified when game status is PENDING"
        )
    
    try:
        # Обновляем настройки
        update_data = settings_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if hasattr(game_service.settings, key):
                setattr(game_service.settings, key, value)
        
        return StandardResponse(
            success=True,
            message="Game settings updated successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating game settings: {str(e)}")


@router.put("/{game_id}/status", response_model=StandardResponse)
async def update_game_status(
    game_id: str,
    status_update: GameStatusUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Изменить статус игры (start/pause/resume)"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        action = status_update.action
        match action:
            case "start":
                if game_service.status != GameStatus.PENDING:
                    raise HTTPException(status_code=400, detail="Game can only be started from PENDING status")
                game_service.start_game()
                message = "Game started successfully"
            
            case "pause":
                if game_service.status != GameStatus.ACTIVE:
                    raise HTTPException(status_code=400, detail="Only active games can be paused")
                game_service.pause_game()
                message = "Game paused successfully"
            
            case "resume":
                if game_service.status != GameStatus.PAUSED:
                    raise HTTPException(status_code=400, detail="Only paused games can be resumed")
                game_service.resume_game()
                message = "Game resumed successfully"
            
            case _:
                raise HTTPException(status_code=400, detail="Invalid action")
        
        return StandardResponse(
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating game status: {str(e)}")


@router.post("/{game_id}/players", response_model=StandardResponse)
async def add_player_to_game(
    game_id: str,
    player_action: PlayerAction,
    current_user: dict = Depends(get_current_user)
):
    """Добавить игрока в игру"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        result = game_service.add_player(
            player_id=player_action.player_id,
            unit_type=player_action.unit_type
        )
        
        if result.get('success'):
            return StandardResponse(
                success=True,
                message=f"Player {player_action.player_id} added to game",
                data=result
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=result.get('message', 'Failed to add player')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding player: {str(e)}")


@router.delete("/{game_id}/players/{player_id}", response_model=StandardResponse)
async def remove_player_from_game(
    game_id: str,
    player_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удалить игрока из игры"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    try:
        result = game_service.remove_player(player_id=player_id)
        
        if result.get('success'):
            return StandardResponse(
                success=True,
                message=f"Player {player_id} removed from game"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=result.get('message', 'Failed to remove player')
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error removing player: {str(e)}")


@router.delete("/{game_id}", response_model=StandardResponse)
async def delete_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Удалить игру (только в статусе PENDING или FINISHED)"""
    coordinator = get_game_coordinator()
    
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if game_service.status not in [GameStatus.PENDING, GameStatus.FINISHED]:
        raise HTTPException(
            status_code=400,
            detail="Game can only be deleted when status is PENDING or FINISHED"
        )
    
    try:
        # Удаляем игру из координатора
        del coordinator.games[game_id]
        
        return StandardResponse(
            success=True,
            message=f"Game {game_id} deleted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting game: {str(e)}")