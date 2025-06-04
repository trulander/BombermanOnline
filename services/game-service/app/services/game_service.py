import random
import time
import math
import json
import logging
from enum import Enum
from typing import Dict, List, Tuple, Optional, Any, Set

from ..entities.map import Map
from ..entities.cell_type import CellType
from ..entities.player import Player
from ..entities.enemy import Enemy, EnemyType
from ..entities.bomb import Bomb
from ..entities.power_up import PowerUp, PowerUpType
from ..entities.game_settings import GameSettings
from ..entities.game_mode import GameModeType
from ..entities.unit_type import UnitType
from ..entities.weapon import WeaponType
from ..services.map_service import MapService
from ..services.game_mode_service import GameModeService
from ..services.modes.campaign_mode import CampaignMode
from ..services.modes.free_for_all_mode import FreeForAllMode
from ..services.modes.capture_flag_mode import CaptureFlagMode
from ..config import settings

logger = logging.getLogger(__name__)


class GameStatus(Enum):
    """Статусы игры"""
    PENDING = "pending"        # Ожидание игроков
    STARTING = "starting"      # Подготовка к запуску
    ACTIVE = "active"          # Активная игра
    PAUSED = "paused"          # Приостановлена
    FINISHED = "finished"      # Завершена


class GameService:
    """Сервис оркестрации игры"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService):
        try:
            self.settings: GameSettings = game_settings
            self.map_service: MapService = map_service
            self.status: GameStatus = GameStatus.PENDING
            
            # Создаем игровой режим в зависимости от настроек
            self.game_mode: GameModeService = self._create_game_mode()
            
            logger.info(f"Game service initialized with mode: {self.settings.game_mode}")
        except Exception as e:
            logger.error(f"Error initializing game service: {e}", exc_info=True)
            raise
    
    def _create_game_mode(self) -> GameModeService:
        """Создать игровой режим на основе настроек"""
        mode_type = self.settings.game_mode
        
        if mode_type == GameModeType.CAMPAIGN:
            return CampaignMode(self.settings, self.map_service)
        elif mode_type == GameModeType.FREE_FOR_ALL:
            return FreeForAllMode(self.settings, self.map_service)
        elif mode_type == GameModeType.CAPTURE_THE_FLAG:
            return CaptureFlagMode(self.settings, self.map_service)
        else:
            logger.warning(f"Unknown game mode {mode_type}, defaulting to campaign")
            return CampaignMode(self.settings, self.map_service)
    
    async def initialize_game(self) -> None:
        """Инициализировать игру"""
        try:
            await self.game_mode.initialize_map()
            self.status = GameStatus.PENDING
            logger.info("Game initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing game: {e}", exc_info=True)
            raise
    
    def add_player(self, player_id: str, unit_type: UnitType = UnitType.BOMBERMAN) -> bool:
        """Добавить игрока в игру"""
        try:
            if self.status not in [GameStatus.PENDING, GameStatus.STARTING]:
                logger.debug(f"Cannot add player {player_id}: game status is {self.status}")
                return False
            
            player = Player(player_id, unit_type)
            success = self.game_mode.add_player(player)
            
            if success:
                logger.info(f"Player {player_id} added with unit type {unit_type.value}")
            
            return success
        except Exception as e:
            logger.error(f"Error adding player {player_id}: {e}", exc_info=True)
            return False
    
    def remove_player(self, player_id: str) -> bool:
        """Удалить игрока из игры"""
        try:
            success = self.game_mode.remove_player(player_id)
            
            # Если игра активна и нет игроков, помечаем как завершенную
            if self.status == GameStatus.ACTIVE and len(self.game_mode.players) == 0:
                self.status = GameStatus.FINISHED
                logger.info("Game marked as finished due to no players")
            
            return success
        except Exception as e:
            logger.error(f"Error removing player {player_id}: {e}", exc_info=True)
            return False
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Получить игрока по ID"""
        return self.game_mode.get_player(player_id)
    
    def start_game(self) -> bool:
        """Запустить игру"""
        try:
            if self.status != GameStatus.PENDING:
                logger.debug(f"Cannot start game: status is {self.status}")
                return False
            
            if len(self.game_mode.players) == 0:
                logger.debug("Cannot start game: no players")
                return False
            
            self.status = GameStatus.ACTIVE
            logger.info("Game started successfully")
            return True
        except Exception as e:
            logger.error(f"Error starting game: {e}", exc_info=True)
            return False
    
    def pause_game(self) -> bool:
        """Приостановить игру"""
        try:
            if self.status != GameStatus.ACTIVE:
                return False
            
            self.status = GameStatus.PAUSED
            logger.info("Game paused")
            return True
        except Exception as e:
            logger.error(f"Error pausing game: {e}", exc_info=True)
            return False
    
    def resume_game(self) -> bool:
        """Возобновить игру"""
        try:
            if self.status != GameStatus.PAUSED:
                return False
            
            self.status = GameStatus.ACTIVE
            logger.info("Game resumed")
            return True
        except Exception as e:
            logger.error(f"Error resuming game: {e}", exc_info=True)
            return False
    
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
            
            return state
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return self.get_state()
    
    def apply_weapon(self, player_id: str, weapon_type: WeaponType) -> bool:
        """Применить оружие игрока"""
        try:
            if self.status != GameStatus.ACTIVE:
                return False
            
            player = self.game_mode.get_player(player_id)
            if not player:
                return False
            
            return self.game_mode.apply_weapon(player, weapon_type)
        except Exception as e:
            logger.error(f"Error applying weapon for player {player_id}: {e}", exc_info=True)
            return False
    
    def assign_player_to_team(self, player_id: str, team_id: str) -> bool:
        """Назначить игрока в команду (для режимов с командами)"""
        try:
            if hasattr(self.game_mode, 'assign_player_to_team'):
                return self.game_mode.assign_player_to_team(player_id, team_id)
            return False
        except Exception as e:
            logger.error(f"Error assigning player {player_id} to team {team_id}: {e}", exc_info=True)
            return False
    
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
            state['gameMode'] = self.settings.game_mode.value
            return state
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            return {
                'error': True,
                'status': self.status.value,
                'gameMode': self.settings.game_mode.value,
                'players': {},
                'teams': {},
                'enemies': [],
                'weapons': [],
                'powerUps': [],
                'map': {'width': self.settings.default_map_width, 'height': self.settings.default_map_height, 
                       'changedCells': [], 'cellSize': self.settings.cell_size},
                'score': 0,
                'level': 1,
                'gameOver': True
            }
    
    def get_teams(self) -> Dict[str, Any]:
        """Получить информацию о командах"""
        try:
            teams_info = {}
            for team_id, player_ids in self.game_mode.teams.items():
                team_players = []
                for player_id in player_ids:
                    player = self.game_mode.get_player(player_id)
                    if player:
                        team_players.append({
                            'id': player_id,
                            'lives': player.lives,
                            'unitType': player.unit_type.value
                        })
                
                teams_info[team_id] = {
                    'players': team_players,
                    'playerCount': len(team_players)
                }
            
            return teams_info
        except Exception as e:
            logger.error(f"Error getting teams info: {e}", exc_info=True)
            return {}


# Поддержка старых методов для совместимости
def place_bomb(game_service: GameService, player: Player) -> bool:
    """Совместимость со старым API"""
    return game_service.apply_weapon(player.id, WeaponType.BOMB) 