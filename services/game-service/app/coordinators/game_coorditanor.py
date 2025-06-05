import asyncio
import logging
import time

from ..config import settings
from ..models.game_create_models import GameCreateSettings
from ..services.game_service import GameService
from ..services.event_service import EventService, NatsEvents
from ..services.map_service import MapService

from ..repositories.map_repository import MapRepository
from ..entities.player import UnitType
from ..entities.game_settings import GameSettings
from ..entities.game_mode import GameModeType
from ..entities.weapon import WeaponType

logger = logging.getLogger(__name__)

class GameCoordinator:
    def __init__(self, notification_service: EventService, map_repository:MapRepository) -> None:
        self.notification_service: EventService = notification_service
        self.map_repository: MapRepository = map_repository
        self.games: dict[str, GameService] = {}


    async def initialize_handlers(self) -> None:
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_CREATE, callback=self.game_create)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_JOIN, callback=self.game_join)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_INPUT, callback=self.game_input)
        await self.notification_service.subscribe_handler(event=NatsEvents.GAME_APPLY_WEAPON, callback=self.game_apply_weapon)
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
            new_game_settings = kwargs.get("new_game_settings")
            if new_game_settings and isinstance(new_game_settings, GameCreateSettings):
                game_settings = GameSettings(**new_game_settings.model_dump())
            else:

                game_settings = GameSettings(
                    game_id=kwargs.get("game_id"),
                    game_mode = kwargs.get("game_mode", GameModeType.CAMPAIGN.value),
                    map_template_id = kwargs.get("map_template_id"),
                    map_chain_id = kwargs.get("map_chain_id")
                )
            #
            # # Создаем настройки игры с новой архитектурой

            
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
            
            # Инициализируем игру
            await game_service.initialize_game()
            
            self.games[game_settings.game_id] = game_service
            logger.info(f"Game {game_settings.game_id} created with mode {game_settings.game_mode}")
            
        except Exception as e:
            logger.error(f"Error creating game {kwargs}: {e}", exc_info=True)
            raise

    async def game_join(self, **kwargs) -> (bool, dict):
        player_id = kwargs.get("player_id")
        game_id = kwargs.get("game_id")
        unit_type_str = kwargs.get("unit_type", UnitType.BOMBERMAN.value)
        
        if game_id not in self.games:
            logger.warning(f"Failed to join game: Game {game_id} not found")
            return False, {"message": "Game not found"}

        try:
            unit_type = UnitType(unit_type_str)
        except ValueError:
            unit_type = UnitType.BOMBERMAN
            
        result = self.games[game_id].add_player(player_id, unit_type)
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


    async def game_apply_weapon(self, **kwargs) -> (bool, dict):
        """Применить оружие игрока (новый универсальный метод)"""
        game_id = kwargs.get("game_id")
        player_id = kwargs.get("player_id")
        weapon_type_str = kwargs.get("weapon_type", "bomb")  # По умолчанию бомба для совместимости

        if game_id in self.games:
            game = self.games[game_id]
            player = game.get_player(player_id)

            if player:
                try:
                    weapon_type = WeaponType(weapon_type_str)
                except ValueError:
                    weapon_type = player.primary_weapon  # Используем основное оружие игрока
                
                result = game.apply_weapon(player_id=player_id, weapon_type=weapon_type)
                response = result, {}
                if result:
                    logger.info(f"Weapon {weapon_type.value} applied by player {player_id} in game {game_id}")
                else:
                    logger.debug(f"Failed to apply weapon {weapon_type.value} for player {player_id} in game {game_id}")
            else:
                response = False, {"message": "Player not found"}
                logger.warning(f"Player {player_id} not found in game {game_id} for apply_weapon")
        else:
            response = False, {"message": "Game not found"}
            logger.warning(f"Game {game_id} not found for apply_weapon")
        return response

    async def game_get_state(self, **kwargs) -> (bool, dict):
        game_id = kwargs.get("game_id")

        if game_id in self.games:
            # Получаем состояние игры
            game_state = self.games[game_id].get_state()

            # Дополнительно получаем полную карту
            if self.games[game_id].game_mode.map:
                full_map = self.games[game_id].game_mode.map.get_map()
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