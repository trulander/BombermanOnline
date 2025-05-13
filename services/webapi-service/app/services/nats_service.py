import json
import logging
from typing import Dict, Any, Callable

import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from ..config import settings

logger = logging.getLogger(__name__)

class NatsService:
    def __init__(self) -> None:
        try:
            self._nc: NATS | None = None
            self.socket_event_handlers: Dict[str, Dict[str, Callable]] = {}
            logger.info("NatsService initialized")
        except Exception as e:
            logger.error(f"Error initializing NatsService: {e}", exc_info=True)
            raise

    async def get_nc(self) -> NATS:
        """Подключение к NATS серверу"""
        try:
            if self._nc is None or self._nc.is_closed:
                logger.info(f"Connecting to NATS server at {settings.NATS_URL}")
                self._nc = await nats.connect(settings.NATS_URL)

                # Подписываемся на обновления игры
                await self._nc.subscribe("game.update.*", cb=self.handle_game_update)
                await self._nc.subscribe("game.over.*", cb=self.handle_game_over)
                await self._nc.subscribe("game.player_disconnected.*", cb=self.handle_player_disconnected)

                logger.info(f"Connected to NATS: {settings.NATS_URL}")
            return self._nc
        except Exception as e:
            logger.error(f"Error connecting to NATS at {settings.NATS_URL}: {e}", exc_info=True)
            raise

    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        try:
            if self._nc:
                logger.info("Disconnecting from NATS server")
                await self._nc.drain()
                self._nc = None
                logger.info("Disconnected from NATS server")
        except Exception as e:
            logger.error(f"Error disconnecting from NATS: {e}", exc_info=True)
            
    def register_socket_handler(
            self, 
            sid: str, 
            event: str, 
            handler: Callable
    ) -> None:
        """Регистрация обработчика сокет-событий"""
        try:
            if f"game_{sid}" not in self.socket_event_handlers:
                self.socket_event_handlers[f"game_{sid}"] = {}
            
            self.socket_event_handlers[f"game_{sid}"][event] = handler
            logger.debug(f"Registered socket handler for SID game_{sid}, event {event}")
        except Exception as e:
            logger.error(f"Error registering socket handler for SID game_{sid}, event {event}: {e}", exc_info=True)
    
    def unregister_socket_handler(self, game_id: str) -> None:
        """Удаление обработчиков сокет-событий"""
        try:
            logger.info(f"Unregistering socket handlers for SID game_{game_id}, handlers: {self.socket_event_handlers}")
            if f"game_{game_id}" in self.socket_event_handlers:
                del self.socket_event_handlers[f"game_{game_id}"]
                logger.info(f"deleted socket handlers for SID game_{game_id}")
        except Exception as e:
            logger.error(f"Error unregistering socket handlers for SID game_{game_id}: {e}", exc_info=True)


    async def handle_game_update(self, msg: Msg) -> None:
        """Обработчик обновления игры"""
        try:
            game_id = msg.subject.split('.')[-1]
            game_state = json.loads(msg.data.decode())
            
            # Отправляем обновление всем подключенным клиентам через сокеты
            handler = self.socket_event_handlers.get(f"game_{game_id}", {}).get('game_update', None)
            if handler:
                await handler(game_id=game_id, game_state=game_state)

            logger.debug(f"Game update for game {game_id} forwarded to {handler} handler")
        except Exception as e:
            logger.error(f"Error handling game update: {e}", exc_info=True)
    
    async def handle_game_over(self, msg: Msg) -> None:
        """Обработчик завершения игры"""
        try:
            game_id = msg.subject.split('.')[-1]
            logger.info(f"Game over event received for game {game_id}")
            
            # Отправляем уведомление всем подключенным клиентам через сокеты
            handler = self.socket_event_handlers.get(f"game_{game_id}", {}).get('game_over', None)
            if handler:
                await handler(game_id=game_id)

            self.unregister_socket_handler(game_id=game_id)

            logger.info(f"Game over for game {game_id} forwarded to {handler} handler")
        except Exception as e:
            logger.error(f"Error handling game over: {e}", exc_info=True)
    
    async def handle_player_disconnected(self, msg: Msg) -> None:
        """Обработчик отключения игрока"""
        try:
            game_id = msg.subject.split('.')[-1]
            data = json.loads(msg.data.decode())
            player_id = data.get('player_id')
            
            logger.info(f"Player {player_id} disconnected from game {game_id}")

            # Отправляем уведомление всем подключенным клиентам в комнату через сокеты
            handler = self.socket_event_handlers.get(f"game_{game_id}", {}).get('player_disconnected', None)
            if handler:
                await handler(game_id=game_id, player_id=player_id)

            logger.debug(f"Player disconnected event for {player_id} in game {game_id} forwarded to {handler} handler")
        except Exception as e:
            logger.error(f"Error handling player disconnect: {e}", exc_info=True)
    
    async def create_game(self, game_id: str) -> Dict[str, Any]:
        """Отправка запроса на создание игры"""
        try:
            nc = await self.get_nc()
            response = await nc.request(
                "game.create",
                json.dumps({"game_id": game_id}).encode(),
                timeout=5.0
            )
            result = json.loads(response.data.decode())
            if result.get('success'):
                logger.info(f"Game created successfully with ID: {game_id}")
            else:
                logger.warning(f"Failed to create game: {result.get('message')}")
            return result
        except Exception as e:
            error_msg = f"Error creating game: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    
    async def join_game(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на присоединение к игре"""
        try:
            nc = await self.get_nc()
            response = await nc.request(
                "game.join",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            result = json.loads(response.data.decode())
            if result.get('success'):
                logger.info(f"Player {player_id} successfully joined game {game_id}")
            else:
                logger.warning(f"Player {player_id} failed to join game {game_id}: {result.get('message')}")
            return result
        except Exception as e:
            error_msg = f"Error joining game: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    
    async def send_input(self, game_id: str, player_id: str, inputs: Dict[str, bool]) -> None:
        """Отправка ввода игрока"""
        logger.debug(f"Sending input for player {player_id} in game {game_id}: {inputs}")
        try:
            nc = await self.get_nc()
            await nc.publish(
                "game.input",
                json.dumps({
                    "game_id": game_id,
                    "player_id": player_id,
                    "inputs": inputs
                }).encode()
            )
        except Exception as e:
            logger.error(f"Error sending input: {e}", exc_info=True)

    
    async def place_bomb(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на установку бомбы"""
        logger.info(f"Player {player_id} placing bomb in game {game_id}")

        try:
            nc = await self.get_nc()
            response = await nc.request(
                "game.place_bomb",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            result = json.loads(response.data.decode())
            if result.get('success'):
                logger.info(f"Bomb placed successfully by player {player_id} in game {game_id}")
            else:
                logger.debug(f"Failed to place bomb for player {player_id} in game {game_id}: {result.get('message')}")
            return result
        except Exception as e:
            error_msg = f"Error placing bomb: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    
    async def get_game_state(self, game_id: str) -> Dict[str, Any]:
        """Получение состояния игры"""
        logger.debug(f"Getting state for game {game_id}")

        try:
            nc = await self.get_nc()
            response = await nc.request(
                "game.get_state",
                json.dumps({"game_id": game_id}).encode(),
                timeout=5.0
            )
            result = json.loads(response.data.decode())
            if result.get('success'):
                logger.debug(f"Successfully retrieved state for game {game_id}")
            else:
                logger.warning(f"Failed to get game state for game {game_id}: {result.get('message')}")
            return result
        except Exception as e:
            error_msg = f"Error getting game state: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}

    
    async def disconnect_player(self, game_id: str, player_id: str) -> Dict[str, Any]:
        """Отправка запроса на отключение игрока"""
        logger.info(f"Disconnecting player {player_id} from game {game_id}")
            
        try:
            nc = await self.get_nc()
            response = await nc.request(
                "game.disconnect",
                json.dumps({"game_id": game_id, "player_id": player_id}).encode(),
                timeout=5.0
            )
            result = json.loads(response.data.decode())
            if result.get('success'):
                logger.info(f"Player {player_id} successfully disconnected from game {game_id}")
            else:
                logger.warning(f"Failed to disconnect player {player_id} from game {game_id}: {result.get('message')}")
            return result
        except Exception as e:
            error_msg = f"Error disconnecting player: {e}"
            logger.error(error_msg, exc_info=True)
            return {"success": False, "message": error_msg}
