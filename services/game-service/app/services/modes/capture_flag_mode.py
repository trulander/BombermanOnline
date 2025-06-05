import logging
from typing import Dict, List, Set
from ..game_mode_service import GameModeService
from ...entities.game_settings import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class CaptureFlagMode(GameModeService):
    """Режим захвата флага"""
    def __init__(self, game_settings: GameSettings, map_service: MapService, team_service=None):
        super().__init__(game_settings, map_service, team_service)
        
        # Отключаем врагов в CTF режиме
        self.settings.enable_enemies = False
        
        # Специфичные для CTF переменные
        self.flag_positions: Dict[str, tuple] = {}  # team_id -> (x, y)
        self.team_flags: Dict[str, str] = {}  # team_id -> flag_id
        self.captured_flags: Set[str] = set()  # Захваченные флаги
        
        self.setup_teams()
    
    def setup_teams(self) -> None:
        """Настроить команды для CTF - команды уже настроены в TeamService"""
        logger.info("CTF mode: team setup completed via TeamService")
    
    def add_player(self, player) -> bool:
        """Добавить игрока в CTF режим"""
        if super().add_player(player):
            logger.info(f"Player {player.id} added to CTF mode")
            return True
        return False
    
    def is_game_over(self) -> bool:
        """Игра заканчивается при достижении лимита очков командой или по времени"""
        if self.team_service:
            # Проверяем лимит очков команд
            for team in self.team_service.get_all_teams():
                if team.score >= self.settings.score_limit:
                    self.game_over = True
                    return True
        
        # TODO: Добавить проверку по времени
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание CTF игры"""
        try:
            winning_team = None
            max_score = 0
            
            if self.team_service:
                for team in self.team_service.get_all_teams():
                    if team.score > max_score:
                        max_score = team.score
                        winning_team = team
            
            if winning_team:
                logger.info(f"CTF mode: Team {winning_team.name} wins with {winning_team.score} points!")
            else:
                logger.info("CTF mode: Game ended in draw")
            
            self.game_over = True
            
        except Exception as e:
            logger.error(f"Error handling CTF game over: {e}", exc_info=True)
            self.game_over = True
    
    def handle_player_hit(self, player) -> None:
        """Переопределяем для режима захвата флага"""
        super().handle_player_hit(player)
        
        # В командном режиме можно добавить респавн если включен
        if player.lives <= 0 and self.settings.respawn_enabled:
            # TODO: Добавить логику респавна
            pass 