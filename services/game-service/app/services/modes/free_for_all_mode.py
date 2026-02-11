import logging
from ..game_mode_service import GameModeService
from ..ai_inference_service import AIInferenceService
from ...models.game_models import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class FreeForAllMode(GameModeService):
    """Режим 'каждый сам за себя'"""
    def __init__(
        self,
        game_settings: GameSettings,
        map_service: MapService,
        team_service=None,
        ai_inference_service: AIInferenceService | None = None,
    ):
        super().__init__(
            game_settings=game_settings,
            map_service=map_service,
            team_service=team_service,
            ai_inference_service=ai_inference_service,
        )
        
        # Отключаем врагов в режиме FFA
        self.settings.enable_enemies = False
        
        self.setup_teams()
    
    def setup_teams(self) -> None:
        """Настроить команды для FFA - команды уже настроены в TeamService"""
        logger.info("FFA mode: team setup completed via TeamService")
    
    def add_player(self, player) -> bool:
        """Добавить игрока в FFA режим"""
        if super().add_player(player):
            logger.info(f"Player {player.id} added to FFA mode")
            return True
        return False
    
    def is_game_over(self) -> bool:
        """Игра заканчивается когда остается один живой игрок или истекает время"""
        alive_players = [p for p in self.players.values() if p.lives > 0]
        
        if len(alive_players) <= 1:
            self.game_over = True
            return True
        
        # TODO: Добавить проверку по времени
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание FFA игры"""
        try:
            alive_players = [p for p in self.players.values() if p.lives > 0]
            
            if len(alive_players) == 1:
                winner = alive_players[0]
                logger.info(f"FFA mode: Player {winner.id} wins!")
                
                # Начисляем очки команде победителя
                if self.team_service:
                    self.team_service.add_score_to_player_team(winner.id, 1000)  # Очки за победу
            else:
                logger.info("FFA mode: Game ended in draw")
            
            self.game_over = True
            
        except Exception as e:
            logger.error(f"Error handling FFA game over: {e}", exc_info=True)
            self.game_over = True
    
    def handle_player_hit(self, player) -> None:
        """Переопределяем для режима все против всех"""
        super().handle_player_hit(player)
        
        # В режиме все против всех убитые игроки исключаются из игры
        if player.lives <= 0:
            logger.info(f"Free for all mode: Player {player.id} eliminated")
            # Можно добавить логику исключения из команды, но игрок остается для просмотра 