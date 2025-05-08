import uuid
from typing import Dict, Any, Callable

# from .socketio_service import SocketIOService
# from ..repositories import RedisRepository
from ..services.nats_service import NatsService

class GameService:
    """
    Служба для управления игровыми сессиями.
    В соответствии с CQRS здесь определяем команды и запросы.
    """
    
    def __init__(
            self,
            nats_service: NatsService,
            # redis_repository: RedisRepository,
            # socket_io_service: SocketIOService
    ) -> None:
        self.nats_service = nats_service

        # Маппинг sid -> player_id и player_id -> sid
        self.sid_user_id_to_player: Dict[str, str] = {}
        self.player_to_sid: Dict[str, str] = {}

        # Маппинг sid -> game_id и game_id -> set(sid)
        self.sid_user_id_to_game: Dict[str, str] = {}
        self.game_to_sids_user_id: Dict[str, set[str]] = {}

    
    # Commands - изменяют состояние системы
    
    async def create_game(self) -> Dict[str, Any]:
        """
        Команда: Создать новую игру
        
        Returns:
            Dict[str, Any]: Результат создания игры
        """
        return await self.nats_service.create_game()
    
    async def join_game(
            self,
            sid_user_id:str,
            game_id: str,
            player_id: str = None
    ) -> Dict[str, Any]:
        """
        Команда: Присоединиться к существующей игре
        
        Args:
            game_id: Идентификатор игры
            player_id: идентификатор игрока
            
        Returns:
            JoinGameResponse: Результат присоединения к игре
        """
        if not player_id:
            player_id = str(uuid.uuid4())
        response = await self.nats_service.join_game(game_id, player_id)

        if response.get('success') and (player_id := response.get('player_id')):
            # Сохраняем привязки
            self.sid_user_id_to_player[sid_user_id] = player_id
            self.player_to_sid[player_id] = sid_user_id
            self.sid_user_id_to_game[sid_user_id] = game_id

            if game_id not in self.game_to_sids_user_id:
                self.game_to_sids_user_id[game_id] = set()

            self.game_to_sids_user_id[game_id].add(sid_user_id)

        return {**response, "player_id": player_id}

    async def register_socket_handler(
            self,
            sid: str,
            event: str,
            handler: Callable
    ) -> None:
        """
        Прокси метод для регистрации слушателя в nats
        """
        self.nats_service.register_socket_handler(sid=sid, event=event, handler=handler)

    async def send_input(self, game_id: str, sid_user_id: str, inputs: Dict[str, bool]) -> None:
        """
        Команда: Отправить ввод игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            inputs: Ввод игрока
        """
        if not game_id or not inputs or sid_user_id not in self.sid_user_id_to_player:
            return

        player_id = self.sid_user_id_to_player[sid_user_id]

        await self.nats_service.send_input(game_id=game_id, player_id=player_id, inputs=inputs)
    
    async def place_bomb(self, game_id: str, sid_user_id: str) -> Dict[str, Any]:
        """
        Команда: Установить бомбу
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат установки бомбы
        """
        if not game_id or sid_user_id not in self.sid_user_id_to_player:
            return {"success": False, "message": "Invalid request"}

        player_id = self.sid_user_id_to_player[sid_user_id]


        return await self.nats_service.place_bomb(game_id, player_id)
    
    async def disconnect_player(self, sid_user_id: str) -> Dict[str, Any]:
        """
        Команда: Отключить игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат отключения игрока
        """

        result = {}

        # Если игрок был в игре, удаляем его из игры
        """Handle socket disconnection and clean up game state"""
        if sid_user_id in self.sid_user_id_to_player and sid_user_id in self.sid_user_id_to_game:
            player_id = self.sid_user_id_to_player[sid_user_id]
            game_id = self.sid_user_id_to_game[sid_user_id]

            result = await self.nats_service.disconnect_player(game_id, player_id)

            # Удаляем обработчики событий
            self.nats_service.unregister_socket_handler(sid=f"game_{game_id}")

        # Удаляем привязки
        if sid_user_id in self.sid_user_id_to_player:
            player_id = self.sid_user_id_to_player[sid_user_id]
            del self.sid_user_id_to_player[sid_user_id]

            if player_id in self.player_to_sid:
                del self.player_to_sid[player_id]

        if sid_user_id in self.sid_user_id_to_game:
            game_id = self.sid_user_id_to_game[sid_user_id]
            del self.sid_user_id_to_game[sid_user_id]

            if game_id in self.game_to_sids_user_id and sid_user_id in self.game_to_sids_user_id[game_id]:
                self.game_to_sids_user_id[game_id].remove(sid_user_id)

                # Если в игре не осталось игроков, удаляем игру
                if not self.game_to_sids_user_id[game_id]:
                    del self.game_to_sids_user_id[game_id]


        return result
    
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