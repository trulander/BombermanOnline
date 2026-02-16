import logging
from ..game_mode_service import GameModeService
from ..ai_inference_service import AIInferenceService
from ...entities import Player
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
        
        # Если таймер активен и истёк — побеждает игрок с наибольшим количеством жизней
        if self.settings.time_limit and self.settings.time_limit > 0 and self.time_remaining <= 0:
            self.game_over = True
            logger.info("FFA mode: Time expired — determining winner by lives")
            return True
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание FFA игры"""
        try:
            alive_players = [p for p in self.players.values() if p.lives > 0]
            
            if len(alive_players) == 1:
                # Остался один живой — он победитель
                winner = alive_players[0]
                logger.info(f"FFA mode: Player {winner.id} wins!")
                
                # Начисляем очки команде победителя
                if self.team_service:
                    self.team_service.add_score_to_player_team(winner.id, 1000)  # Очки за победу
            elif len(alive_players) > 1:
                # Время истекло — побеждает игрок с наибольшим количеством жизней
                max_lives: int = max(p.lives for p in alive_players)
                top_players = [p for p in alive_players if p.lives == max_lives]
                if len(top_players) == 1:
                    winner = top_players[0]
                    logger.info(f"FFA mode: Player {winner.id} wins by most lives ({max_lives})!")
                    if self.team_service:
                        self.team_service.add_score_to_player_team(winner.id, 1000)
                else:
                    # Ничья — у нескольких игроков одинаковое количество жизней
                    logger.info(f"FFA mode: Game ended in draw ({len(top_players)} players with {max_lives} lives)")
            else:
                logger.info("FFA mode: Game ended in draw")
            
            self.game_over = True
            
        except Exception as e:
            logger.error(f"Error handling FFA game over: {e}", exc_info=True)
            self.game_over = True
    
    def handle_player_hit(self, player: Player, attacker_id: str = None) -> None:
        """Переопределяем для режима все против всех"""
        super().handle_player_hit(player=player, attacker_id=attacker_id)
        
        # В режиме все против всех убитые игроки исключаются из игры
        if player.lives <= 0:
            logger.info(f"Free for all mode: Player {player.id} eliminated")
            # Можно добавить логику исключения из команды, но игрок остается для просмотра 