import logging
from ..game_mode_service import GameModeService
from ...entities.game_settings import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class FreeForAllMode(GameModeService):
    """Режим все против всех - каждый игрок в своей команде"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService):
        super().__init__(game_settings, map_service)
        self.settings.enable_enemies = False  # В PvP режиме нет врагов
        self.setup_teams()
    
    def setup_teams(self) -> None:
        """Настроить команды для режима все против всех"""
        self.teams = {}
        logger.info("Free for all mode: teams will be created per player")
    
    def add_player(self, player) -> bool:
        """Добавить игрока в режим все против всех"""
        if super().add_player(player):
            # Каждый игрок в своей команде
            team_id = f"team_{player.id}"
            player.set_team(team_id)
            self.teams[team_id] = [player.id]
            logger.info(f"Player {player.id} added to own team {team_id} in free for all mode")
            return True
        return False
    
    def is_game_over(self) -> bool:
        """Игра заканчивается когда остается один живой игрок или достигнут лимит очков/времени"""
        alive_players = [p for p in self.players.values() if p.lives > 0]
        
        # Если остался только один живой игрок
        if len(alive_players) <= 1:
            self.game_over = True
            return True
        
        # Проверка лимита времени
        if self.settings.time_limit:
            elapsed_time = self.last_update_time - self.last_update_time  # TODO: добавить правильный подсчет времени
            if elapsed_time >= self.settings.time_limit:
                self.game_over = True
                return True
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание игры в режиме все против всех"""
        try:
            alive_players = [p for p in self.players.values() if p.lives > 0]
            
            if len(alive_players) == 1:
                winner = alive_players[0]
                logger.info(f"Free for all mode: Player {winner.id} wins!")
            elif len(alive_players) == 0:
                logger.info("Free for all mode: No survivors - draw!")
            else:
                logger.info("Free for all mode: Time limit reached - game over")
            
            self.game_over = True
            
        except Exception as e:
            logger.error(f"Error handling free for all game over: {e}", exc_info=True)
            self.game_over = True
    
    def handle_player_hit(self, player) -> None:
        """Переопределяем для режима все против всех"""
        super().handle_player_hit(player)
        
        # В режиме все против всех убитые игроки исключаются из игры
        if player.lives <= 0:
            logger.info(f"Free for all mode: Player {player.id} eliminated")
            # Можно добавить логику исключения из команды, но игрок остается для просмотра 