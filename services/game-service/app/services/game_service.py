import logging
from typing import Dict, Optional, Any
from ..entities.player import Player, UnitType
from ..models.game_models import GameSettings
from ..entities.game_mode import GameModeType
from ..entities.weapon import WeaponType
from ..entities.game_status import GameStatus
from ..services.map_service import MapService
from ..services.game_mode_service import GameModeService
from ..services.team_service import TeamService
from ..services.modes.campaign_mode import CampaignMode
from ..services.modes.free_for_all_mode import FreeForAllMode
from ..services.modes.capture_flag_mode import CaptureFlagMode
from ..config import settings
from datetime import datetime

logger = logging.getLogger(__name__)


class GameService:
    """Сервис оркестрации игры"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService):
        try:
            self.settings: GameSettings = game_settings
            self.map_service: MapService = map_service
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
                return CampaignMode(self.settings, self.map_service, self.team_service)

            case GameModeType.FREE_FOR_ALL:
                return FreeForAllMode(self.settings, self.map_service, self.team_service)

            case GameModeType.CAPTURE_THE_FLAG:
                return CaptureFlagMode(self.settings, self.map_service, self.team_service)

            case _:
                logger.warning(f"Unknown game mode {self.settings.game_mode}, defaulting to campaign")
                return CampaignMode(self.settings, self.map_service, self.team_service)


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


    def add_player(self, player_id: str, unit_type: UnitType = UnitType.BOMBERMAN) -> dict:
        """Добавить игрока в игру"""
        try:
            if self.status not in [GameStatus.PENDING, GameStatus.STARTING]:
                message = f"Cannot add player {player_id}: game status is {self.status}"
                logger.debug(message)
                return {
                    "success": False,
                    "message": message
                }
            
            player = Player(player_id, unit_type)
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
                if self.status == GameStatus.ACTIVE and len(self.game_mode.players) == 0:
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

    async def update(self) -> Dict[str, Any]:
        """Обновить состояние игры"""
        try:
            if self.status != GameStatus.ACTIVE:
                return self.get_state()
            
            # Делегируем обновление игровому режиму
            state = await self.game_mode.update()
            
            # Проверяем завершение игры
            if self.game_mode.game_over:
                self.status = GameStatus.FINISHED
                logger.info("Game finished")

            self.updated_at = datetime.utcnow()
            
            return state
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return self.get_state()
    
    def apply_weapon(self, player_id: str, weapon_type: WeaponType) -> dict:
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
            
            result = self.game_mode.apply_weapon(player, weapon_type)
            if result:
                self.updated_at = datetime.utcnow()
                return {"success": True, "message": "Weapon applied successfully"}
            else:
                message = f"Failed to apply weapon {weapon_type.value} for player {player_id}."
                logger.warning(message)
                return {"success": False, "message": message}
        except Exception as e:
            message = f"Error applying weapon for player {player_id}: {e}"
            logger.error(message, exc_info=True)
            return {"success": False, "message": message}

    
    def is_active(self) -> bool:
        """Проверить активность игры"""
        try:
            if self.status == GameStatus.FINISHED:
                return False
            
            return self.game_mode.is_active()
        except Exception as e:
            logger.error(f"Error checking if game is active: {e}", exc_info=True)
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Получить состояние игры"""
        try:
            state = self.game_mode.get_state()
            state['status'] = self.status.value

            # Добавляем состояние команд из TeamService
            state['teams'] = self.team_service.get_teams_state()
            return state
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            return {
                'error': True,
                'status': self.status.value,
                'players': {},
                'teams': {},
                'enemies': [],
                'weapons': [],
                'powerUps': [],
                'map': {
                    'changedCells': [],
                },
                'score': 0,
                'level': 1,
                'gameOver': True
            }