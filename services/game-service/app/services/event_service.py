import asyncio
import json
import logging
from enum import Enum
from typing import Dict, Any, Callable, Awaitable
from nats.aio.msg import Msg
from ..repositories.nats_repository import NatsRepository


logger = logging.getLogger(__name__)


class NatsEvents(Enum):
    GAME_CREATE = "game.create"
    GAME_JOIN = "game.join"
    GAME_INPUT = "game.input"
    GAME_PLACE_BOMB = "game.place_bomb"
    GAME_GET_STATE = "game.get_state"
    GAME_DISCONNECT = "game.disconnect"


class EventService:
    def __init__(self, nats_repository: NatsRepository) -> None:
        try:
            self.nats_repository = nats_repository
            self._subscriptions = []
            logger.info("EventService initialized")
        except Exception as e:
            logger.error(f"Error initializing EventService: {e}", exc_info=True)
            raise

    async def subscribe_handler(self, event: NatsEvents, callback: Callable) -> None:
        def subscribe_wrapper(handler: Callable) -> Any:
            async def callback_wrapper(msg: Msg) -> None:
                try:
                    decoded_data = json.loads(msg.data.decode())
                    response = await handler(data=decoded_data, callback=callback)
                    if msg.reply:
                        await self.nats_repository.publish_simple(
                            subject=msg.reply,
                            payload=response
                        )
                except Exception as e:
                    error_msg = f"Error creating game: {e}"
                    logger.error(error_msg, exc_info=True)
                    if msg and msg.reply:
                        await self.nats_repository.publish_simple(
                            subject=msg.reply,
                            payload={
                                "success": False,
                                "message": error_msg
                            }
                        )

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

        await self.nats_repository.subscribe(subject=event.value, callback=cb)

    async def disconnect(self) -> None:
        """Отключение от NATS сервера"""
        await self.nats_repository.disconnect()

    async def send_game_update(self, game_id: str, data: dict) -> bool:
        """Отправка обновления игры"""
        return await self.nats_repository.publish_event(
            subject_base="game.update",
            payload=data,
            game_id=game_id
        )

    async def send_game_over(self, game_id: str) -> bool:
        """Отправка события окончания игры"""
        return await self.nats_repository.publish_event(
            subject_base="game.over",
            payload={},
            game_id=game_id
        )

    async def handle_create_game(self, data: dict, callback: Callable) -> dict:
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

    async def handle_join_game(self, data: dict, callback: Callable) -> dict:
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

    async def handle_input(self, data: dict, callback: Callable) -> None:
        """Обработчик ввода игрока"""
        await callback(**data)

    async def handle_place_bomb(self, data: dict, callback: Callable) -> dict:
        """Обработчик размещения бомбы"""
        status, result = await callback(**data)
        return {"success": status, **result}

    async def handle_get_game_state(self, data: dict, callback: Callable) -> dict:
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

    async def handle_player_disconnect(self, data: dict, callback: Callable) -> dict:
        """Обработчик отключения игрока"""
        game_id = data.get("game_id")
        player_id = data.get("player_id")
        status, result = await callback(**data)
        if status:
            # Уведомляем других игроков об отключении
            await self.nats_repository.publish_event(
                subject_base="game.player_disconnected",
                payload={"player_id": player_id},
                game_id=game_id
            )
            logger.info(f"Sent player_disconnected notification for player {player_id} in game {game_id}")
            return {"success": True}
        return {"success": False, **result} 