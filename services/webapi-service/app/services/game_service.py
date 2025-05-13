import uuid
import logging
from typing import Dict, Any, Callable
from ..services.nats_service import NatsService

logger = logging.getLogger(__name__)

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
        try:
            logger.debug("Initializing GameService")
            self.nats_service = nats_service

            # Маппинг sid -> player_id и player_id -> sid
            self.sid_user_id_to_player: Dict[str, str] = {}
            self.player_to_sid: Dict[str, str] = {}

            # Маппинг sid -> game_id и game_id -> set(sid)
            self.sid_user_id_to_game: Dict[str, str] = {}
            self.game_to_sids_user_id: Dict[str, set[str]] = {}
            
            logger.info("GameService initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing GameService: {e}", exc_info=True)
            raise
    
    # Commands - изменяют состояние системы
    
    async def create_game(self) -> Dict[str, Any]:
        """
        Команда: Создать новую игру
        
        Returns:
            Dict[str, Any]: Результат создания игры
        """
        try:
            logger.info("Creating new game")
            game_id = str(uuid.uuid4())
            logger.info(f"Creating new game with ID: {game_id}")
            result = await self.nats_service.create_game(game_id=game_id)
            if result.get('success'):
                logger.info(f"Game created successfully with ID: {result.get('game_id')}")
            else:
                logger.warning(f"Failed to create game: {result.get('message')}")
            return result
        except Exception as e:
            logger.error(f"Error creating game: {e}", exc_info=True)
            return {"success": False, "message": f"Error creating game: {str(e)}"}
    
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
        try:
            if not player_id:
                player_id = str(uuid.uuid4())
                logger.debug(f"Generated new player ID: {player_id}")
                
            logger.info(f"Joining game {game_id} with player ID {player_id}")
            response = await self.nats_service.join_game(game_id, player_id)

            if response.get('success') and (player_id := response.get('player_id')):
                # Сохраняем привязки
                logger.debug(f"Saving mappings for SID {sid_user_id} to player {player_id} in game {game_id}")
                self.sid_user_id_to_player[sid_user_id] = player_id
                self.player_to_sid[player_id] = sid_user_id
                self.sid_user_id_to_game[sid_user_id] = game_id

                if game_id not in self.game_to_sids_user_id:
                    self.game_to_sids_user_id[game_id] = set()

                self.game_to_sids_user_id[game_id].add(sid_user_id)
                logger.info(f"Player {player_id} successfully joined game {game_id}")
            else:
                logger.warning(f"Failed to join game {game_id}: {response.get('message')}")

            return {**response, "player_id": player_id}
        except Exception as e:
            logger.error(f"Error joining game {game_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error joining game: {str(e)}", "player_id": player_id}

    async def register_socket_handler(
            self,
            sid: str,
            event: str,
            handler: Callable
    ) -> None:
        """
        Прокси метод для регистрации слушателя в nats
        """
        try:
            logger.debug(f"Registering socket handler for SID {sid}, event {event}")
            self.nats_service.register_socket_handler(sid=sid, event=event, handler=handler)
            logger.debug(f"Socket handler registered successfully for SID {sid}, event {event}")
        except Exception as e:
            logger.error(f"Error registering socket handler for SID {sid}, event {event}: {e}", exc_info=True)
            raise

    async def send_input(self, game_id: str, sid_user_id: str, inputs: Dict[str, bool]) -> None:
        """
        Команда: Отправить ввод игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            inputs: Ввод игрока
        """
        try:
            if not game_id:
                logger.warning("Cannot send input: missing game_id")
                return
                
            if not inputs:
                logger.warning(f"Cannot send input for game {game_id}: empty inputs")
                return
                
            if sid_user_id not in self.sid_user_id_to_player:
                logger.warning(f"Cannot send input for game {game_id}: SID {sid_user_id} not associated with any player")
                return

            player_id = self.sid_user_id_to_player[sid_user_id]
            logger.debug(f"Sending inputs for player {player_id} in game {game_id}: {inputs}")

            await self.nats_service.send_input(game_id=game_id, player_id=player_id, inputs=inputs)
            logger.debug(f"Input sent successfully for player {player_id} in game {game_id}")
        except Exception as e:
            logger.error(f"Error sending input for SID {sid_user_id} in game {game_id}: {e}", exc_info=True)
    
    async def place_bomb(self, game_id: str, sid_user_id: str) -> Dict[str, Any]:
        """
        Команда: Установить бомбу
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат установки бомбы
        """
        try:
            if not game_id:
                logger.warning("Cannot place bomb: missing game_id")
                return {"success": False, "message": "Missing game_id"}
                
            if sid_user_id not in self.sid_user_id_to_player:
                logger.warning(f"Cannot place bomb in game {game_id}: SID {sid_user_id} not associated with any player")
                return {"success": False, "message": "Invalid player"}

            player_id = self.sid_user_id_to_player[sid_user_id]
            logger.debug(f"Player {player_id} is placing a bomb in game {game_id}")

            result = await self.nats_service.place_bomb(game_id, player_id)
            
            if result.get('success'):
                logger.debug(f"Bomb placed successfully by player {player_id} in game {game_id}")
            else:
                logger.debug(f"Failed to place bomb for player {player_id} in game {game_id}: {result.get('message')}")
                
            return result
        except Exception as e:
            error_msg = f"Error placing bomb for SID {sid_user_id} in game {game_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}
    
    async def disconnect_player(self, sid_user_id: str) -> Dict[str, Any]:
        """
        Команда: Отключить игрока
        
        Args:
            game_id: Идентификатор игры
            player_id: Идентификатор игрока
            
        Returns:
            Dict[str, Any]: Результат отключения игрока
        """
        try:
            logger.debug(f"Disconnecting player with SID {sid_user_id}")
            result = {}

            # Если игрок был в игре, удаляем его из игры
            if sid_user_id in self.sid_user_id_to_player and sid_user_id in self.sid_user_id_to_game:
                player_id = self.sid_user_id_to_player[sid_user_id]
                game_id = self.sid_user_id_to_game[sid_user_id]
                
                logger.info(f"Player {player_id} disconnecting from game {game_id}")
                result = await self.nats_service.disconnect_player(game_id, player_id)

                # Удаляем обработчики событий
                try:
                    logger.debug(f"Unregistering socket handlers for game {game_id}")
                    self.nats_service.unregister_socket_handler(sid=f"game_{game_id}")
                except Exception as e:
                    logger.warning(f"Error unregistering socket handlers for game {game_id}: {e}")

            # Удаляем привязки
            player_id = None
            if sid_user_id in self.sid_user_id_to_player:
                player_id = self.sid_user_id_to_player[sid_user_id]
                logger.debug(f"Removing mapping SID {sid_user_id} -> player {player_id}")
                del self.sid_user_id_to_player[sid_user_id]

                if player_id in self.player_to_sid:
                    logger.debug(f"Removing mapping player {player_id} -> SID {sid_user_id}")
                    del self.player_to_sid[player_id]

            game_id = None
            if sid_user_id in self.sid_user_id_to_game:
                game_id = self.sid_user_id_to_game[sid_user_id]
                logger.debug(f"Removing mapping SID {sid_user_id} -> game {game_id}")
                del self.sid_user_id_to_game[sid_user_id]

                if game_id in self.game_to_sids_user_id and sid_user_id in self.game_to_sids_user_id[game_id]:
                    logger.debug(f"Removing SID {sid_user_id} from game {game_id} players list")
                    self.game_to_sids_user_id[game_id].remove(sid_user_id)

                    # Если в игре не осталось игроков, удаляем игру
                    if not self.game_to_sids_user_id[game_id]:
                        logger.debug(f"No players left in game {game_id}, removing game from tracking")
                        del self.game_to_sids_user_id[game_id]

            logger.info(f"Player successfully disconnected: SID={sid_user_id}, player_id={player_id}, game_id={game_id}")
            return result
        except Exception as e:
            logger.error(f"Error disconnecting player with SID {sid_user_id}: {e}", exc_info=True)
            return {"success": False, "message": f"Error disconnecting player: {str(e)}"}
    
    # Queries - не изменяют состояние, только запрашивают данные
    
    async def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """
        Запрос: Получить состояние игры
        
        Args:
            game_id: Идентификатор игры
            
        Returns:
            Dict[str, Any]: Состояние игры
        """
        try:
            logger.debug(f"Getting state for game {game_id}")
            response = await self.nats_service.get_game_state(game_id)
            
            if response.get('success'):
                logger.debug(f"Successfully retrieved state for game {game_id}")
            else:
                logger.warning(f"Failed to get state for game {game_id}: {response.get('message')}")
                
            return response
        except Exception as e:
            error_msg = f"Error getting game state for game {game_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg} 