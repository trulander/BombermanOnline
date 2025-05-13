import asyncio
import json
import logging
from enum import Enum
from functools import wraps
from typing import Dict, Any, Callable, Awaitable
import nats
from nats.aio.client import Client as NATS
from nats.aio.msg import Msg

from ..config import settings
from ..services.game_service import GameService

logger = logging.getLogger(__name__)

class NatsEvents(Enum):
    GAME_CREATE = "game.create"
    GAME_JOIN = "game.join"
    GAME_INPUT = "game.input"
    GAME_PLACE_BOMB = "game.place_bomb"
    GAME_GET_STATE = "game.get_state"
    GAME_DISCONNECT = "game.disconnect"

class NatsService:
    def __init__(self) -> None:
        self._nc: NATS | None = None
        try:
            self._subscriptions = []
            # self.games: Dict[str, GameService] = {}
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

                logger.info(f"Connected to NATS: {settings.NATS_URL}")
            return self._nc
        except Exception as e:
            logger.error(f"Error connecting to NATS at {settings.NATS_URL}: {e}", exc_info=True)
            raise

    async def subscribe_handler(self, event: NatsEvents, callback: Callable) -> None:
        def subscribe_wrapper(handler) -> Any:
            async def callback_wrapper(msg: Msg) -> None:
                try:
                    decoded_data = json.loads(msg.data.decode())
                    response = await handler(data=decoded_data, callback=callback)
                    if msg.reply:
                        nc = await self.get_nc()
                        await nc.publish(msg.reply, json.dumps(response).encode())
                except Exception as e:
                    error_msg = f"Error creating game: {e}"
                    logger.error(error_msg, exc_info=True)
                    if msg and msg.reply:
                        nc = await self.get_nc()
                        await nc.publish(msg.reply, json.dumps({"success": False, "message": error_msg}).encode())

            return callback_wrapper
        match event:
            case NatsEvents.GAME_CREATE:
                cb = subscribe_wrapper(handler=self.handle_create_game)
            case NatsEvents.GAME_JOIN:
                cb = subscribe_wrapper(handler=self.handle_join_game)
            case NatsEvents.GAME_INPUT:
                cb = subscribe_wrapper(handler=self.handle_input)
            case NatsEvents.GAME_PLACE_BOMB:
                cb = subscribe_wrapper(handler=self.handle_place_bomb)
            case NatsEvents.GAME_GET_STATE:
                cb = subscribe_wrapper(handler=self.handle_get_game_state)
            case NatsEvents.GAME_DISCONNECT:
                cb = subscribe_wrapper(handler=self.handle_player_disconnect)
            case _:
                pass

        nc = await self.get_nc()
        await nc.subscribe(event.value, cb=cb)

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

    async def send_game_update(self, game_id, data: dict):
        nc = await self.get_nc()
        await nc.publish(f"game.update.{game_id}", json.dumps(data).encode())

    async def send_game_over(self, game_id):
        nc = await self.get_nc()
        await nc.publish(f"game.over.{game_id}", b"")


    async def handle_create_game(self, data: dict, callback) -> dict:
        """Обработчик создания новой игры"""
        print(data)
        game_id = data.get("game_id")
        if game_id:
            await callback(game_id=game_id)
            response = {"success": True, "game_id": game_id}
            logger.info(f"Game created with ID: {game_id}")
        else:
            response = {"success": False, "message": "Missing game_id"}
            logger.warning("Failed to create game: Missing game_id")
        return response

    async def handle_join_game(self, data: dict, callback) -> dict:
        """Обработчик присоединения к игре"""
        game_id = data.get("game_id")
        player_id = data.get("player_id")

        if not game_id or not player_id:
            response = {"success": False, "message": "Missing game_id or player_id"}
            logger.warning(f"Failed to join game: Missing game_id or player_id. Data: {data}")
        else:
            status, result = await callback(game_id=game_id, player_id=player_id)
            if status:
                response = {
                    "success": True,
                    "player_id": player_id,
                    "game_state": result.get("game_state"),
                }
                logger.info(f"Player {player_id} joined game {game_id}")
            else:
                response = {"success": False, "message": result.get("message")}
                logger.warning(f"Failed to join game: Game {game_id} {result.get("message")}")
        return response

    async def handle_input(self, data: dict, callback) -> None:
        """Обработчик ввода игрока"""
        await callback(**data)

    async def handle_place_bomb(self, data: dict, callback) -> dict:
        """Обработчик размещения бомбы"""
        status, result = await callback(**data)
        return {"success": status, **result}
            

    
    async def handle_get_game_state(self, data: dict, callback) -> dict:
        """Обработчик получения состояния игры"""
        game_id = data.get("game_id")
        status, result = await callback(**data)
        if status:
            response = {
                "success": True, **result
            }
            logger.debug(f"State requested for game {game_id}")
        else:
            response = {"success": False, **result}

        return response


    async def handle_player_disconnect(self, data: dict, callback) -> dict:
        """Обработчик отключения игрока"""

        game_id = data.get("game_id")
        player_id = data.get("player_id")
        status, result = await callback(**data)
        if status:
            # Уведомляем других игроков об отключении
            nc = await self.get_nc()
            await nc.publish(
                f"game.player_disconnected.{game_id}",
                json.dumps({"player_id": player_id}).encode()
            )
            logger.info(f"Sent player_disconnected notification for player {player_id} in game {game_id}")
            return {"success": True}
        return {"success": False, **result}
