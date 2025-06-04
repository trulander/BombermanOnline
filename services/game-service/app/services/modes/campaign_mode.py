import logging
from ..game_mode_service import GameModeService
from ...entities.game_settings import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class CampaignMode(GameModeService):
    """Режим прохождения с возможностью кооператива"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService):
        super().__init__(game_settings, map_service)
        self.setup_teams()
    
    def setup_teams(self) -> None:
        """Настроить команды для режима прохождения - одна команда"""
        self.teams = {"team_1": []}
        logger.info("Campaign mode: single team created")
    
    def add_player(self, player) -> bool:
        """Добавить игрока в режим прохождения"""
        if super().add_player(player):
            # Автоматически добавляем всех игроков в одну команду
            player.set_team("team_1")
            self.teams["team_1"].append(player.id)
            logger.info(f"Player {player.id} added to team_1 in campaign mode")
            return True
        return False
    
    def is_game_over(self) -> bool:
        """Игра заканчивается когда все игроки мертвы или все враги убиты"""
        # Проверяем есть ли живые игроки
        alive_players = [p for p in self.players.values() if p.lives > 0]
        if not alive_players:
            self.game_over = True
            return True
        
        # Проверяем завершение уровня (все враги убиты)
        if self.settings.enable_enemies and len(self.enemies) == 0:
            return True
        
        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание игры в режиме прохождения"""
        try:
            alive_players = [p for p in self.players.values() if p.lives > 0]
            
            if not alive_players:
                # Все игроки мертвы - поражение
                self.game_over = True
                logger.info("Campaign mode: All players dead - game over")
            elif self.settings.enable_enemies and len(self.enemies) == 0:
                # Уровень завершен - переход на следующий уровень
                await self._level_complete()
                logger.info(f"Campaign mode: Level {self.level} completed")
            
        except Exception as e:
            logger.error(f"Error handling campaign game over: {e}", exc_info=True)
            self.game_over = True
    
    async def _level_complete(self) -> None:
        """Обработать завершение уровня"""
        try:
            self.level += 1
            self.score += self.settings.level_complete_score
            
            # Сброс карты для следующего уровня
            await self.initialize_map()
            
            # Очистка оружия и усилений
            self.weapons = {}
            self.power_ups = {}
            
            # Сброс позиций игроков
            spawn_positions = self.map.get_player_spawn_positions()
            if not spawn_positions:
                spawn_positions = [(1, 1), (self.map.width - 2, 1), 
                                 (1, self.map.height - 2), (self.map.width - 2, self.map.height - 2)]
            
            for i, player in enumerate(self.players.values()):
                if i < len(spawn_positions):
                    x, y = spawn_positions[i]
                    player.x = x * self.settings.cell_size
                    player.y = y * self.settings.cell_size
                    
        except Exception as e:
            logger.error(f"Error handling level completion: {e}", exc_info=True) 