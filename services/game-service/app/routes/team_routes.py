from typing import List
from fastapi import APIRouter, HTTPException, Depends, status

from app.auth import get_current_user
from app.coordinators.game_coorditanor import GameCoordinator
from app.models.team_models import Team, TeamCreate, TeamUpdate, PlayerTeamAction, TeamDistributionRequest

from app.entities.game_status import GameStatus


router = APIRouter(prefix="/teams", tags=["teams"])


def get_game_coordinator() -> GameCoordinator:
    """Dependency для получения GameCoordinator."""
    # TODO: Заменить на правильную инъекцию зависимости
    from app.main import game_coordinator
    return game_coordinator


@router.get("/{game_id}", response_model=List[Team])
async def get_teams(
    game_id: str,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> List[Team]:
    """Получить список команд для игры."""
    game_service = coordinator.get_game(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    teams = game_service.team_service.get_all_teams()
    return [Team(**team.to_dict()) for team in teams]


@router.post("/{game_id}", response_model=Team, status_code=status.HTTP_201_CREATED)
async def create_team(
    game_id: str,
    team_data: TeamCreate,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> Team:
    """Создать новую команду в игре."""
    game_service = coordinator.get_game(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команды можно создавать только в играх со статусом PENDING"
        )
    
    try:
        team = game_service.team_service.create_team(team_data.name)
        return Team(**team.to_dict())
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/{game_id}/{team_id}", response_model=Team)
async def update_team(
    game_id: str,
    team_id: str,
    team_data: TeamUpdate,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> Team:
    """Обновить команду."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команды можно редактировать только в играх со статусом PENDING"
        )
    
    team = game_service.team_service.update_team(team_id, name=team_data.name)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )
    
    return Team(**team.to_dict())


@router.delete("/{game_id}/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    game_id: str,
    team_id: str,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> None:
    """Удалить команду."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Команды можно удалять только в играх со статусом PENDING"
        )
    
    if not game_service.team_service.delete_team(team_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда не найдена"
        )


@router.post("/{game_id}/{team_id}/players", response_model=Team)
async def add_player_to_team(
    game_id: str,
    team_id: str,
    action: PlayerTeamAction,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> Team:
    """Добавить игрока в команду."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Игроков можно добавлять в команды только в играх со статусом PENDING"
        )
    
    # Проверяем, что игрок существует в игре
    player = game_service.get_player(action.player_id)
    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игрок не найден в игре"
        )
    
    try:
        if not game_service.team_service.add_player_to_team(team_id, action.player_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Команда не найдена"
            )
        
        # Обновляем team_id у игрока
        player.set_team(team_id)
        
        team = game_service.team_service.get_team(team_id)
        return Team(**team.to_dict())
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{game_id}/{team_id}/players/{player_id}", response_model=Team)
async def remove_player_from_team(
    game_id: str,
    team_id: str,
    player_id: str,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> Team:
    """Удалить игрока из команды."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Игроков можно удалять из команд только в играх со статусом PENDING"
        )
    
    if not game_service.team_service.remove_player_from_team(team_id, player_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Команда или игрок не найдены"
        )
    
    # Очищаем team_id у игрока
    player = game_service.get_player(player_id)
    if player:
        player.set_team("")
    
    team = game_service.team_service.get_team(team_id)
    return Team(**team.to_dict())


@router.post("/{game_id}/distribute", response_model=List[Team])
async def distribute_players(
    game_id: str,
    request: TeamDistributionRequest,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> List[Team]:
    """Автоматически распределить игроков по командам."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    if game_service.status != GameStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Игроков можно распределять по командам только в играх со статусом PENDING"
        )
    
    # Получаем всех игроков в игре
    players = list(game_service.game_mode.players.values())
    
    # Выполняем автоматическое распределение
    game_service.team_service.auto_distribute_players(players, request.redistribute_existing)
    
    # Обновляем team_id у игроков
    for player in players:
        team = game_service.team_service.get_player_team(player.id)
        if team:
            player.set_team(team.id)
    
    teams = game_service.team_service.get_all_teams()
    return [Team(**team.to_dict()) for team in teams]


@router.get("/{game_id}/validate")
async def validate_teams(
    game_id: str,
    current_user: dict = Depends(get_current_user),
    coordinator: GameCoordinator = Depends(get_game_coordinator)
) -> dict:
    """Проверить корректность настройки команд."""
    game_service = coordinator.games.get(game_id)
    if not game_service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Игра не найдена"
        )
    
    errors = game_service.team_service.validate_teams()
    
    return {
        "is_valid": len(errors) == 0,
        "errors": errors
    } 