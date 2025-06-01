import asyncio
import json
import logging
import time

from ..config import settings
from ..services.game_service import GameService
from ..services.nats_service import NatsService, NatsEvents
from ..services.map_service import MapService

from ..repositories.map_repository import MapRepository
from ..entities.player import Player
from ..entities.game_settings import GameSettings, GameModeSettings
from ..entities.game_mode import GameModeType

logger = logging.getLogger(__name__)

class GameCoordinator:
    def __init__(self, notification_service: NatsService) -> None:
        try:
            self.notification_service: NatsService = notification_service

            self.games: dict[str, GameService] = {}
            
            # Инициализируем сервисы
            self.map_repository: MapRepository = MapRepository()
            
            logger.info("GameCoordinator initialized")
        except Exception as e:
            logger.error(f"Error initializing GameCoordinator: {e}", exc_info=True)
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
            
            # Используем настройки FPS из конфигурации
            fps = settings.GAME_UPDATE_FPS
            interval = 1 / fps
            
            while True:
                active_games = 0
                start_time = time.time()
                
                for game_id, game in list(self.games.items()):
                    if game.is_active():
                        active_games += 1
                        updated_state = await game.update()
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

    async def game_create(self, **kwargs) -> None:
        """Создать новую игру с настройками"""
        try:
            game_id = kwargs.get("game_id")
            game_mode_type = kwargs.get("game_mode", GameModeType.SINGLE_PLAYER.value)
            map_template_id = kwargs.get("map_template_id")
            map_chain_id = kwargs.get("map_chain_id")
            map_group_id = kwargs.get("map_group_id")
            
            # Создаем настройки игрового режима
            game_mode_settings = GameModeSettings(
                mode_type=GameModeType(game_mode_type),
                map_chain_id=map_chain_id,
                map_group_id=map_group_id
            )
            
            # Создаем настройки игры
            game_settings = GameSettings(
                cell_size=settings.CELL_SIZE,
                default_map_width=settings.MAP_WIDTH,
                default_map_height=settings.MAP_HEIGHT,
                game_mode=game_mode_settings
            )
            
            # Создаем сервис карт
            map_service = MapService(
                map_repository=self.map_repository,
                game_settings=game_settings
            )
            
            # Создаем игру
            game_service = GameService(
                game_settings=game_settings,
                map_service=map_service
            )
            
            # Инициализируем продвинутую карту асинхронно
            await game_service.initialize_advanced_map()
            
            self.games[game_id] = game_service
            logger.info(f"Game {game_id} created with mode {game_mode_type}")
            
        except Exception as e:
            logger.error(f"Error creating game {game_id}: {e}", exc_info=True)
            raise

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
            if self.games[game_id].map:
                full_map = self.games[game_id].map.get_map()
            else:
                full_map = {"grid": [], "width": 0, "height": 0}
                
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
            status_removing = game.remove_player(player_id)
            logger.info(f"Player {player_id} disconnected from game {game_id}")
            return status_removing, {"message": "Player disconnected"}
        else:
            if not game_id:
                logger.warning("Missing game_id in disconnect request")
            elif game_id not in self.games:
                logger.warning(f"Game {game_id} not found for disconnect")
            elif not player_id:
                logger.warning(f"Missing player_id in disconnect request for game {game_id}")
            return False, {}