import logging
from ..game_mode_service import GameModeService
from ...entities.game_settings import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class CaptureFlagMode(GameModeService):
    """Режим захвата флага - команды определяются картой"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService):
        super().__init__(game_settings, map_service)
        self.settings.enable_enemies = False  # В PvP режиме нет врагов
        self.flag_positions = []  # Позиции флагов
        self.team_flags = {}  # team_id -> flag_position
        self.captured_flags = {}  # team_id -> count
        self.setup_teams()
    
    def setup_teams(self) -> None:
        """Настроить команды для режима захвата флага"""
        # Команды будут настроены после загрузки карты на основе количества флагов
        self.teams = {}
        logger.info("Capture flag mode: teams will be set up based on map flags")
    
    async def initialize_map(self) -> None:
        """Инициализировать карту и настроить флаги"""
        await super().initialize_map()
        self._setup_flags_and_teams()
    
    def _setup_flags_and_teams(self) -> None:
        """Настроить флаги и команды на основе карты"""
        try:
            # TODO: Добавить специальный тип клетки для флагов в CellType
            # Пока используем фиксированное количество команд
            team_count = max(2, self.settings.team_count)
            
            for i in range(team_count):
                team_id = f"team_{i+1}"
                self.teams[team_id] = []
                self.captured_flags[team_id] = 0
            
            logger.info(f"Capture flag mode: {team_count} teams created")
            
        except Exception as e:
            logger.error(f"Error setting up flags and teams: {e}", exc_info=True)
    
    def add_player(self, player) -> bool:
        """Добавить игрока в режим захвата флага"""
        if super().add_player(player):
            # Автоматически распределяем игроков по командам
            team_id = self._assign_player_to_team()
            player.set_team(team_id)
            self.teams[team_id].append(player.id)
            logger.info(f"Player {player.id} added to {team_id} in capture flag mode")
            return True
        return False
    
    def _assign_player_to_team(self) -> str:
        """Автоматически назначить игрока в команду с наименьшим количеством игроков"""
        min_players = float('inf')
        best_team = None
        
        for team_id, player_ids in self.teams.items():
            if len(player_ids) < min_players:
                min_players = len(player_ids)
                best_team = team_id
        
        return best_team or "team_1"
    
    def assign_player_to_team(self, player_id: str, team_id: str) -> bool:
        """Ручное назначение игрока в команду"""
        try:
            player = self.players.get(player_id)
            if not player:
                return False
            
            if team_id not in self.teams:
                return False
            
            # Удаляем из старой команды
            old_team = player.team_id
            if old_team and old_team in self.teams:
                if player_id in self.teams[old_team]:
                    self.teams[old_team].remove(player_id)
            
            # Добавляем в новую команду
            player.set_team(team_id)
            self.teams[team_id].append(player_id)
            logger.info(f"Player {player_id} manually assigned to {team_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error assigning player {player_id} to team {team_id}: {e}", exc_info=True)
            return False
    
    def is_game_over(self) -> bool:
        """Игра заканчивается когда команда достигает лимита очков или времени"""
        # Проверка лимита очков
        if self.settings.score_limit:
            for team_id, flags_captured in self.captured_flags.items():
                if flags_captured >= self.settings.score_limit:
                    self.game_over = True
                    return True
        
        # Проверка лимита времени
        if self.settings.time_limit:
            elapsed_time = self.last_update_time - self.last_update_time  # TODO: добавить правильный подсчет времени
            if elapsed_time >= self.settings.time_limit:
                self.game_over = True
                return True
        
        # Проверка есть ли живые игроки в командах
        alive_teams = 0
        for team_id, player_ids in self.teams.items():
            team_has_alive_players = any(
                self.players[pid].lives > 0 
                for pid in player_ids 
                if pid in self.players
            )
            if team_has_alive_players:
                alive_teams += 1
        
        if alive_teams <= 1:
            self.game_over = True
            return True
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание игры в режиме захвата флага"""
        try:
            # Определяем победителя по количеству захваченных флагов
            winning_team = max(self.captured_flags.items(), key=lambda x: x[1])
            logger.info(f"Capture flag mode: Team {winning_team[0]} wins with {winning_team[1]} flags!")
            
            self.game_over = True
            
        except Exception as e:
            logger.error(f"Error handling capture flag game over: {e}", exc_info=True)
            self.game_over = True
    
    def handle_player_hit(self, player) -> None:
        """Переопределяем для режима захвата флага"""
        super().handle_player_hit(player)
        
        # В командном режиме можно добавить респавн если включен
        if player.lives <= 0 and self.settings.respawn_enabled:
            # TODO: Добавить логику респавна
            pass 