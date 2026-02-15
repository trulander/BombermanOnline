import logging
import time
from typing import Dict, Optional, Any

from ..entities.bomberman import Bomberman
from ..entities.player import Player, UnitType
from ..entities.tank import Tank
from ..models.game_models import GameSettings, GameTeamInfo, GameUpdateEvent
from ..entities.game_mode import GameModeType
from ..entities.weapon import WeaponType, WeaponAction
from ..entities.game_status import GameStatus
from ..models.map_models import MapState, MapData, MapUpdate
from ..services.map_service import MapService
from ..services.ai_inference_service import AIInferenceService
from ..services.game_mode_service import GameModeService
from ..services.team_service import TeamService
from ..services.modes.campaign_mode import CampaignMode
from ..services.modes.free_for_all_mode import FreeForAllMode
from ..services.modes.capture_flag_mode import CaptureFlagMode
from ..config import settings
from datetime import datetime


logger = logging.getLogger(__name__)


MapState.model_rebuild()

class GameService:
    """Сервис оркестрации игры"""
    
    def __init__(
        self,
        game_settings: GameSettings,
        map_service: MapService,
        ai_inference_service: AIInferenceService,
    ):
        try:
            self.settings: GameSettings = game_settings
            self.map_service: MapService = map_service
            self.ai_inference_service: AIInferenceService = ai_inference_service
            self.status: GameStatus = GameStatus.PENDING
            self.created_at: datetime = datetime.utcnow()
            self.updated_at: datetime = datetime.utcnow()
            
            # Инициализируем сервис команд
            self.team_service: TeamService = TeamService(team_mode_settings=self.settings.team_mode_settings)
            
            # Создаем игровой режим в зависимости от настроек
            self.game_mode: GameModeService = self._create_game_mode()
            
            logger.info(f"Game service initialized with mode: {self.settings.game_mode}")
        except Exception as e:
            logger.error(f"Error initializing game service: {e}", exc_info=True)
            raise


    def _create_game_mode(self) -> GameModeService:
        """Создать игровой режим на основе настроек"""
        match self.settings.game_mode:
            case GameModeType.CAMPAIGN:
                return CampaignMode(
                    game_settings=self.settings,
                    map_service=self.map_service,
                    team_service=self.team_service,
                    ai_inference_service=self.ai_inference_service,
                )

            case GameModeType.FREE_FOR_ALL:
                return FreeForAllMode(
                    game_settings=self.settings,
                    map_service=self.map_service,
                    team_service=self.team_service,
                    ai_inference_service=self.ai_inference_service,
                )

            case GameModeType.CAPTURE_THE_FLAG:
                return CaptureFlagMode(
                    game_settings=self.settings,
                    map_service=self.map_service,
                    team_service=self.team_service,
                    ai_inference_service=self.ai_inference_service,
                )

            case _:
                logger.warning(f"Unknown game mode {self.settings.game_mode}, defaulting to campaign")
                return CampaignMode(
                    game_settings=self.settings,
                    map_service=self.map_service,
                    team_service=self.team_service,
                    ai_inference_service=self.ai_inference_service,
                )


    async def initialize_game(self) -> None:
        """Инициализировать игру"""
        try:
            # Настраиваем команды по умолчанию для режима
            self.team_service.setup_default_teams()
            
            await self.game_mode.initialize_map()
            self.status = GameStatus.PENDING
            self.updated_at = datetime.utcnow()
            logger.info("Game initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing game: {e}", exc_info=True)
            raise


    def add_player(self, player_id: str, unit_type: UnitType = UnitType.BOMBERMAN, ai_player: bool = False) -> dict:
        """Добавить игрока в игру"""
        try:
            if self.status not in [GameStatus.PENDING]:
                message = f"Cannot add player {player_id}: game status is {self.status}"
                logger.debug(message)
                return {
                    "success": False,
                    "message": message
                }

            match unit_type:
                case UnitType.BOMBERMAN:
                    player = Bomberman(
                        id=player_id,
                        size=self.settings.cell_size,
                        map=self.game_mode.map,
                        settings=self.settings,
                        ai=ai_player
                    )
                case UnitType.TANK:
                    player = Tank(
                        id=player_id,
                        size=self.settings.cell_size,
                        map=self.game_mode.map,
                        settings=self.settings,
                        ai=ai_player
                    )
                case _:
                    player = Bomberman(
                        id=player_id,
                        size=self.settings.cell_size,
                        map=self.game_mode.map,
                        settings=self.settings,
                        ai=ai_player
                    )
            success = self.game_mode.add_player(player)
            
            if success:
                # Автоматически распределяем игрока по командам если настроено
                self.team_service.auto_distribute_players([player])
                
                # Обновляем team_id у игрока
                team = self.team_service.get_player_team(player.id)
                if team:
                    player.set_team(team.id)
                
                self.updated_at = datetime.utcnow()
                logger.info(f"Player {player_id} added with unit type {unit_type.value}")
                return {
                    "success": True,
                    "message": f"Player {player_id} added",
                    "player_id": player.id
                }
            else:
                message = f"Failed to add player {player_id} to game mode."
                logger.warning(message)
                return {
                    "success": False,
                    "message": message
                }
        except Exception as e:
            message = f"Error adding player {player_id}: {e}"
            logger.error(message, exc_info=True)
            return {
                "success": False,
                "message": message
            }


    def remove_player(self, player_id: str) -> dict:
        """Удалить игрока из игры"""
        try:
            # Удаляем игрока из команд
            self.team_service.remove_player_from_team(player_id)
            
            success = self.game_mode.remove_player(player_id)
            
            if success:
                # Если игра активна и нет игроков, помечаем как завершенную
                if self.is_active() and len(self.game_mode.players) == 0:
                    self.status = GameStatus.FINISHED
                    logger.info("Game marked as finished due to no players")
                self.updated_at = datetime.utcnow()
                return {
                    "success": True,
                    "message": f"Player {player_id} removed"
                }
            else:
                message = f"Player {player_id} not found in game mode."
                logger.warning(message)
                return {
                    "success": False,
                    "message": message
                }
        except Exception as e:
            message = f"Error removing player {player_id}: {e}"
            logger.error(message, exc_info=True)
            return {
                "success": False,
                "message": message
            }


    def get_player(self, player_id: str) -> Optional[Player]:
        """Получить игрока по ID"""
        return self.game_mode.get_player(player_id)


    def start_game(self) -> dict:
        """Запустить игру"""
        try:
            if self.status != GameStatus.PENDING:
                message = f"Cannot start game: status is {self.status}"
                logger.debug(message)
                return {
                    "success": False,
                    "message": message
                }
            
            if len(self.game_mode.players) == 0:
                message = "Cannot start game: no players"
                logger.debug(message)
                return {
                    "success": False,
                    "message": message
                }
            
            # Проверяем корректность настройки команд
            validation_errors = self.team_service.validate_teams()
            if validation_errors:
                message = f"Team validation errors: {validation_errors}"
                logger.warning(message)
                # Можно либо блокировать запуск, либо предупредить
                # В данном случае только предупреждаем
            
            self.status = GameStatus.ACTIVE
            self.updated_at = datetime.utcnow()
            logger.info("Game started successfully")
            return {
                "success": True,
                "message": "Game started successfully"
            }
        except Exception as e:
            message = f"Error starting game: {e}"
            logger.error(message, exc_info=True)
            return {
                "success": False,
                "message": message
            }
    
    def pause_game(self) -> dict:
        """Приостановить игру"""
        try:
            if self.status != GameStatus.ACTIVE:
                message = f"Cannot pause game: status is {self.status}"
                logger.debug(message)
                return {
                    "success": False,
                    "message": message
                }

            self.status = GameStatus.PAUSED
            self.updated_at = datetime.utcnow()
            logger.info("Game paused")
            return {"success": True, "message": "Game paused successfully"}
        except Exception as e:
            message = f"Error pausing game: {e}"
            logger.error(message, exc_info=True)
            return {"success": False, "message": message}

    def resume_game(self) -> dict:
        """Возобновить игру"""
        try:
            if self.status != GameStatus.PAUSED:
                message = f"Cannot resume game: status is {self.status}"
                logger.debug(message)
                return {"success": False, "message": message}

            self.status = GameStatus.ACTIVE
            self.updated_at = datetime.utcnow()
            logger.info("Game resumed")
            return {"success": True, "message": "Game resumed successfully"}
        except Exception as e:
            message = f"Error resuming game: {e}"
            logger.error(message, exc_info=True)
            return {"success": False, "message": message}

    async def update(self, *, delta_seconds: float | None = None) -> GameUpdateEvent:
        """Обновить состояние игры"""
        try:
            if not self.is_active():
                logger.debug("game is not active yet.")
                return GameUpdateEvent(
                    game_id=self.settings.game_id,
                    status=self.status,
                    is_active=False,
                )
            
            # Делегируем обновление игровому режиму
            status_update = await self.game_mode.update(delta_time=delta_seconds)
            state = GameUpdateEvent(
                game_id=self.settings.game_id,
                map_update=self.game_mode.map.get_changes(),
                status=self.status,
                is_active=self.is_active(),
                **status_update
            )

            # Проверяем завершение игры
            if self.game_mode.game_over:
                self.status = GameStatus.FINISHED
                logger.info("Game finished")

            self.updated_at = datetime.utcnow()
            
            return state
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return GameUpdateEvent(
                game_id=self.settings.game_id,
                status=self.status,
                is_active=False,
                error=True,
                message=f"Error in game update: {e}"
            )

    
    def place_weapon(self, player_id: str, weapon_action: WeaponAction) -> dict:
        """Применить оружие игрока"""
        try:
            if self.status != GameStatus.ACTIVE:
                message = f"Cannot apply weapon: game status is {self.status}"
                logger.debug(message)
                return {"success": False, "message": message}
            
            player = self.game_mode.get_player(player_id)
            if not player:
                message = f"Player {player_id} not found to apply weapon."
                logger.warning(message)
                return {"success": False, "message": message}
            
            result = self.game_mode.place_weapon(player, weapon_action)
            if result:
                self.updated_at = datetime.utcnow()
                return {"success": True, "message": "Weapon applied successfully"}
            else:
                message = f"Failed to apply weapon {weapon_action.value} for player {player_id}."
                logger.warning(message)
                return {"success": False, "message": message}
        except Exception as e:
            message = f"Error applying weapon for player {player_id}: {e}"
            logger.error(message, exc_info=True)
            return {"success": False, "message": message}



    def is_active(self) -> bool:
        """Проверить активность игры"""
        try:
            if self.status in [GameStatus.FINISHED, GameStatus.PAUSED, GameStatus.PENDING]:
                return False
            
            return self.game_mode.is_active()
        except Exception as e:
            logger.error(f"Error checking if game is active: {e}", exc_info=True)
            return False
    
    def get_state(self) -> MapState:
        """Получить состояние игры"""
        try:
            state = self.game_mode.get_state()
            state.status = self.status.value
            state.is_active = self.is_active()

            # Добавляем состояние команд из TeamService
            state.teams = {id: GameTeamInfo(**team) for id, team in self.team_service.get_teams_state().items()}
            return state
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            return MapState(
                players={},
                enemies={},
                weapons={},
                power_ups={},
                map=MapData(grid=None, width=0, height=0),
                level=0,
                error=True,
                is_active=False
            )