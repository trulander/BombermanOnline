import uuid
from typing import Dict, Any

from ..models.game import GameState, JoinGameResponse
from ..services.nats_service import NatsService

class GameService:
    """
    Служба для управления игровыми сессиями.
    В соответствии с CQRS здесь определяем команды и запросы.
    """
    
    def __init__(self, nats_service: NatsService) -> None:
        self.nats_service = nats_service
    
    # Commands - изменяют состояние системы
    
    async def create_game(self) -> Dict[str, Any]:
        """
        Команда: Создать новую игру
        
        Returns:
            Dict[str, Any]: Результат создания игры
        """
        return await self.nats_service.create_game()
    
    async def join_game(self, game_id: str) -> JoinGameResponse:
        """
        Команда: Присоединиться к существующей игре
        
        Args:
            game_id: Идентификатор игры
            
        Returns:
            JoinGameResponse: Результат присоединения к игре
        """
        player_id = str(uuid.uuid4())
        response = await self.nats_service.join_game(game_id, player_id)
        
        if response.get("success"):
            return JoinGameResponse(
                game_id=game_id,
                player_id=player_id,
                success=True
            )
        else:
            return JoinGameResponse(
                game_id=game_id,
                player_id=player_id,
                success=False,
                message=response.get("message", "Неизвестная ошибка")
            )
    
    async def send_input(self, game_id: str, player_id: str, inputs: Dict[str, bool]) -> None:
        """
        Команда: Отправить ввод игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            inputs: Ввод игрока
        """
        await self.nats_service.send_input(game_id, player_id, inputs)
    
    async def place_bomb(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Команда: Установить бомбу
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат установки бомбы
        """
        return await self.nats_service.place_bomb(game_id, player_id)
    
    async def disconnect_player(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """
        Команда: Отключить игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат отключения игрока
        """
        return await self.nats_service.disconnect_player(game_id, player_id)
    
    # Queries - не изменяют состояние, только запрашивают данные
    
    async def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """
        Запрос: Получить состояние игры
        
        Args:
            game_id: Идентификатор игры
            
        Returns:
            Dict[str, Any]: Состояние игры
        """
        response = await self.nats_service.get_game_state(game_id)
        return response 