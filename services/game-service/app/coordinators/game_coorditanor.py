import asyncio
import json
import logging
import time

from ..config import settings
from ..services.game_service import GameService
from ..services.nats_service import NatsService, NatsEvents
from ..entities.player import Player


logger = logging.getLogger(__name__)

class GameCoordinator:
    def __init__(self, notification_service: NatsService) -> None:
        try:
            self.notification_service: NatsService = notification_service
            self.games: dict[str, GameService] = {}
        except Exception as e:
            logger.error(f"Error initializing NatsService: {e}", exc_info=True)
            raise

    async def initialize_handlers(self) -> None:
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_CREATE, callback=self.game_create)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_JOIN, callback=self.game_join)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_INPUT, callback=self.game_input)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_PLACE_BOMB, callback=self.game_place_bomb)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_GET_STATE, callback=self.game_get_state)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_DISCONNECT, callback=self.game_player_disconnect)


    async def start_game_loop(self) -> None:
        """Запуск игрового цикла"""
        try:
            logger.info("Starting game loop")
            fps = settings.GAME_UPDATE_FPS  # Например, 30
            interval = 1 / fps
            while True:
                active_games = 0
                start_time = time.time()
                for game_id, game in list(self.games.items()):
                    if game.is_active():
                        active_games += 1
                        updated_state = game.update()
                        # Отправляем обновление через NATS всем подключенным клиентам
                        await self.notification_service.send_game_update(game_id=game_id, data=updated_state)
                    else:
                        # Игра окончена, отправляем уведомление всем игрокам
                        logger.info(f"Game {game_id} is over or has no players, sending game over notification")
                        await self.notification_service.send_game_over(game_id=game_id)
                        del self.games[game_id]

                if active_games > 0:
                    logger.debug(f"Game loop update: {active_games} active games")

                time_difference = interval - (time.time() - start_time)
                sleep_duration = max(0, time_difference)
                await asyncio.sleep(sleep_duration)
        except Exception as e:
            logger.error(f"Error in game loop: {e}", exc_info=True)

    async def game_create(self, game_id: str):
        self.games[game_id] = GameService()

    async def game_join(self, **kwargs) -> (bool, dict):
        player_id = kwargs.get("player_id")
        game_id = kwargs.get("game_id")
        if game_id not in self.games:
            logger.warning(f"Failed to join game: Game {game_id} not found")
            return False, {"message": "Game not found"}

        player = Player(player_id)
        result = self.games[game_id].add_player(player)
        if result:
            # Получаем начальное состояние игры с данными для текущего игрока
            return True, {"game_state": self.games[game_id].get_state()}
        return False, {"message": "Game is full"}

    async def game_input(self, **kwargs) -> None:
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")
        inputs = kwargs.get("inputs")

        if game_id in self.games:
            game = self.games[game_id]
            player = game.get_player(player_id)

            if player:
                player.set_inputs(inputs)
                logger.debug(f"Input received for player {player_id} in game {game_id}: {inputs}")
            else:
                logger.warning(f"Player {player_id} not found in game {game_id} for input")
        else:
            logger.warning(f"Game {game_id} not found for input")

    async def game_place_bomb(self, **kwargs) -> (bool, dict):
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")

        if game_id in self.games:
            game = self.games[game_id]
            player = game.get_player(player_id)

            if player:
                result = game.place_bomb(player)
                response = result, {}
                if result:
                    logger.info(f"Bomb placed by player {player_id} in game {game_id}")
                else:
                    logger.debug(f"Failed to place bomb for player {player_id} in game {game_id}")
            else:
                response = False, {"message": "Player not found"}
                logger.warning(f"Player {player_id} not found in game {game_id} for place_bomb")
        else:
            response = False, {"message": "Game not found"}
            logger.warning(f"Game {game_id} not found for place_bomb")
        return response


    async def game_get_state(self, **kwargs) -> (bool, dict):
        game_id = kwargs.get("game_id")

        if game_id in self.games:
            # Получаем состояние игры
            game_state = self.games[game_id].get_state()

            # Дополнительно получаем полную карту
            full_map = self.games[game_id].map.get_map()
            logger.debug(f"State requested for game {game_id}")
            return True, {"game_state": game_state, "full_map": full_map}
        else:
            logger.warning(f"Game {game_id} not found for get_game_state")
            return False, {"message": "Game not found"}


    async def game_player_disconnect(self, **kwargs) -> (bool, dict):
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")

        if game_id and game_id in self.games and player_id:
            game = self.games[game_id]
            game.remove_player(player_id)
            logger.info(f"Player {player_id} disconnected from game {game_id}")

            if len(game.players) == 0:
                logger.info(f"No players left in game {game_id}, removing game")
                del self.games[game_id]
                return False, {}
            else:
                return True, {}
        else:
            if not game_id:
                logger.warning("Missing game_id in disconnect request")
            elif game_id not in self.games:
                logger.warning(f"Game {game_id} not found for disconnect")
            elif not player_id:
                logger.warning(f"Missing player_id in disconnect request for game {game_id}")
            return False, {}