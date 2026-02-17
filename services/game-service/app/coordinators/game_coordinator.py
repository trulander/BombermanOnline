import asyncio
import logging
import time

from ..config import settings
from ..models.game_models import GameCreateSettings, GameSettings
from ..services.game_service import GameService
from ..services.ai_inference_service import AIInferenceService
from ..services.event_service import EventService, NatsEvents
from ..services.map_service import MapService

from ..repositories.map_repository import MapRepository
from ..entities.game_mode import GameModeType
from ..entities.weapon import WeaponAction

logger = logging.getLogger(__name__)

class GameCoordinator:
    def __init__(
        self,
        notification_service: EventService,
        map_repository: MapRepository,
        ai_inference_service: AIInferenceService,
    ) -> None:
        self.notification_service: EventService = notification_service
        self.map_repository: MapRepository = map_repository
        self.ai_inference_service = ai_inference_service
        self.games: dict[str, GameService] = {}


    async def initialize_handlers(self) -> None:
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_CREATE, callback=self.game_create)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_JOIN, callback=self.game_join)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_INPUT, callback=self.game_input)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_PLACE_WEAPON, callback=self.game_place_weapon)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_GET_STATE, callback=self.game_get_state)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_DISCONNECT, callback=self.game_player_disconnect)

    async def start_game_loop(self) -> None:
        """Запуск игрового цикла"""
        logger.info("Starting game loop")

        # Используем настройки FPS из конфигурации
        fps = settings.GAME_UPDATE_FPS
        interval = 1 / fps

        while True:
            try:
                active_games = 0
                start_time = time.time()

                for game_id, game in list(self.games.items()):
                    if game.game_mode.is_alive() and game.is_active():
                        active_games += 1
                        updated_state = await game.update(delta_seconds=None)
                        # Отправляем обновление через NATS всем подключенным клиентам
                        await self.notification_service.send_game_update(data=updated_state.model_dump(mode="json"))
                    elif game.is_active() and not game.game_mode.is_game_over():
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

    async def game_create(self, **kwargs) -> dict:
        """Создать новую игру с настройками"""
        try:
            new_game_settings = kwargs.get("new_game_settings")
            game_id = kwargs.get("game_id")
            logger.info(f"Creating new game settings for game {game_id}, kwargs: {kwargs}")


            if new_game_settings and isinstance(new_game_settings, GameCreateSettings):
                game_settings = GameSettings(**new_game_settings.model_dump())
            else:

                game_settings = GameSettings(
                    game_mode = kwargs.get("game_mode", GameModeType.CAMPAIGN.value),
                    map_template_id = kwargs.get("map_template_id"),
                    map_chain_id = kwargs.get("map_chain_id")
                )
            game_settings.game_id = game_id
            # Создаем сервис карт
            map_service = MapService(
                map_repository=self.map_repository,
                game_settings=game_settings
            )
            
            # Создаем игру
            game_service = GameService(
                game_settings=game_settings,
                map_service=map_service,
                ai_inference_service=self.ai_inference_service,
            )
            
            # Инициализируем игру
            await game_service.initialize_game()
            
            self.games[game_settings.game_id] = game_service
            logger.info(f"Game {game_settings.game_id} created with mode {game_settings.game_mode}")
            return {
                "success": True,
                "game_id": game_settings.game_id
            }
            
        except Exception as e:
            logger.error(f"Error creating game {kwargs}: {e}", exc_info=True)
            return {
                "success": False,
                "message": str(e)
            }


    async def game_join(self, **kwargs) -> dict:
        player_id = kwargs.get("player_id")
        game_id = kwargs.get("game_id")
        # unit_type_str = kwargs.get("unit_type", UnitType.BOMBERMAN.value)
        
        if game_id not in self.games:
            logger.warning(f"Failed to join game: Game {game_id} not found")
            return {
                "success": False,
                "message": "Game not found"
            }
        self.games[game_id].game_mode.update_player_connection_status(player_id=player_id, connected=True)

        return {
            "success": True,
            "message": f"Player {player_id} joined game {game_id}"
        }

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
                pass
                #TODO исправить frontend чтобы он не отправлял комманты на input до старта игры.
                # logger.warning(f"Player {player_id} not found in game {game_id} for input")
        else:
            logger.warning(f"Game {game_id} not found for input")


    async def game_place_weapon(self, **kwargs) -> dict:
        """Применить оружие игрока (новый универсальный метод)"""
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")
        weapon_action = WeaponAction(kwargs.get("weapon_action", WeaponAction.PLACEWEAPON1))

        if not game_id in self.games:
            logger.warning(f"Game {game_id} not found for place_weapon")
            return {
                "success": False,
                "message": "Game not found"
            }

        game = self.games[game_id]
        player = game.get_player(player_id)

        if player:
            result = game.place_weapon(player_id=player_id, weapon_action=weapon_action)

            logger.info(f"Weapon {weapon_action.value} applied by player {player_id} in game {game_id}, result: {result}")
            return result

        else:
            logger.warning(f"Player {player_id} not found in game {game_id} for place_weapon")
            return {
                "success": False,
                "message": "Player not found"
            }


    async def game_get_state(self, **kwargs) -> dict:
        game_id = kwargs.get("game_id")

        if game_id in self.games:
            game_service = self.games[game_id]
            game_state = game_service.get_state()

            result = {
                "success": True,
                "game_state": game_state.model_dump(mode="json"),
            }
            logger.debug(f"State requested for game game_id: {game_id}, result: {result}")
            return result
        else:
            logger.warning(f"Game {game_id} not found for get_game_state")
            return {
                "success": False,
                "message": "Game not found"
            }

    async def game_player_disconnect(self, **kwargs) -> dict:
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")

        if game_id and game_id in self.games and player_id:
            game = self.games[game_id]
            game.game_mode.update_player_connection_status(player_id=player_id, connected=False)
            logger.info(f"Player {player_id} disconnected from game {game_id}")
            return {
                    "success": True,
                    "message": f"Player {player_id} disconnected from game {game_id}"
                }
        else:
            if not game_id:
                logger.warning("Missing game_id in disconnect request")
                return {
                    "success": False,
                    "message": "Missing game_id"
                }
            elif game_id not in self.games:
                logger.warning(f"Game {game_id} not found for disconnect")
                return {
                    "success": False,
                    "message": "Game not found"
                }
            elif not player_id:
                logger.warning(f"Missing player_id in disconnect request for game {game_id}")
                return {
                    "success": False,
                    "message": "Missing player_id"
                }
            return {
                "success": False,
                "message": "Unknown error during disconnect"
            }