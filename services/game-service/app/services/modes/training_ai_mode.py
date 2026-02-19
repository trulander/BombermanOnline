import logging
import random
import time
from collections import defaultdict

from ..ai_action_mapper import action_to_inputs, action_to_direction, inputs_to_action, direction_to_action
from ..ai_observation import build_observation
from ..game_mode_service import GameModeService
from ..ai_inference_service import AIInferenceService
from ...entities import Enemy, Player, Entity
from ...entities.enemy import EnemyUpdate
from ...entities.player import PlayerUpdate
from ...entities.weapon import Weapon, WeaponUpdate, WeaponAction
from ...models.game_models import GameSettings
from ...services.map_service import MapService

logger = logging.getLogger(__name__)


class TrainingAiMode(GameModeService):
    """Режим прохождения с возможностью кооператива"""
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
        self.setup_teams()

    async def update(self, *, delta_time: float | None = None) -> dict:
        """Обновить состояние игры и вернуть новое состояние"""
        try:
            # Вычисляем delta time
            current_time: float = time.time()
            self.last_update_time = current_time

            # Декрементируем обратный таймер если он активен
            if self.time_remaining > 0:
                self.time_remaining = max(0.0, self.time_remaining - delta_time)

            # Пропускаем обновление если игра окончена
            if self.game_over:
                logger.debug("Game is over, skipping update")
                return {}

            result = defaultdict(dict)
            # await self._apply_ai_actions(delta_time=delta_time)
            # Обновляем игроков
            for player in list(self.players.values()):
                result["players_update"].update({player.id: self.update_player(player=player, delta_time=delta_time)})

            # Обновляем врагов если включены
            if self.settings.enable_enemies:
                for enemy in list(self.enemies):
                    result["enemies_update"].update({enemy.id: self.update_enemy(enemy=enemy, delta_time=delta_time)})

            # Обновляем оружие
            for weapon in list(self.weapons.values()):
                result["weapons_update"].update({weapon.id: self.update_weapon(weapon=weapon, delta_time=delta_time)})

            for power_up in self.power_ups.values():
                result["power_ups_update"].update({power_up.id: power_up.get_changes()})

            # Передаём оставшееся время в результат обновления
            if self.time_remaining > 0 or (self.settings.time_limit and self.settings.time_limit > 0):
                result["time_remaining"] = self.time_remaining

            # Проверяем завершение игры
            if self.is_game_over():
                await self.handle_game_over()
            logger.debug(f"Game update event: {result}")
            return result

        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return {}

    def update_player(self, player: Player, delta_time: float) -> PlayerUpdate | None:
        """Обновить одного игрока"""
        try:
            if not player.is_alive():
                return player.get_changes()

            if player.ai and player.can_handle_ai_action():
                self._handle_ai_action(entity=player, is_cooperative=False)

            is_player_moved: bool = player.update(delta_time=delta_time)
            self.team_service.add_score_to_player_team(
                player_id=player.id,
                points=self.settings.player_moved_score if is_player_moved else self.settings.played_did_not_moved_score
            )

            # Проверка коллизии с усилениями
            for power_up in list(self.power_ups.values()):
                if self.check_entity_collision(entity1=player, entity2=power_up):
                    logger.info(f"Player {player.id} collected powerup {power_up.type.name}")
                    self.apply_power_up(player, power_up)

            # Проверка коллизии с врагами
            if not player.invulnerable and self.settings.enable_enemies:
                for enemy in self.enemies:
                    if not enemy.destroyed and self.check_entity_collision(entity1=player, entity2=enemy):
                        logger.info(f"Player {player.id} hit by enemy {enemy.type.value}")
                        self.handle_player_hit(player=player, attacker_id=enemy.id)
            return player.get_changes()

        except Exception as e:
            logger.error(f"Error updating player {player.id}: {e}", exc_info=True)

    def handle_player_hit(self, player: Player, attacker_id: str = None) -> None:
        """Обработать попадание в игрока"""
        try:
            is_hit = player.set_hit()
            if is_hit:
                if player.id == attacker_id:
                    #если икрок и атакующий одно и тоже, то самострел
                    self.team_service.add_score_to_player_team(player_id=player.id, points=self.settings.hit_by_itself_score)
                else:
                    # если игрок и нападающий разные, то попадание от врага
                    if player.destroyed:
                        self.team_service.add_score_to_player_team(player_id=player.id, points=self.settings.killed_by_enemy_score)
                        self.team_service.add_score_to_player_team(player_id=attacker_id, points=self.settings.player_destroy_score)
                    else:
                        self.team_service.add_score_to_player_team(player_id=player.id, points=self.settings.hit_by_enemy_score)
                        self.team_service.add_score_to_player_team(player_id=attacker_id, points=self.settings.player_hit_score)


        except Exception as e:
            logger.error(f"Error handling player hit for player {player.id}: {e}", exc_info=True)

    def update_enemy(self, enemy: Enemy, delta_time: float) -> EnemyUpdate | None:
        """Обновить одного врага"""
        try:
            if enemy.destroyed:
                self._cancel_ai_task(enemy.id)
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= self.settings.destroy_animation_time:
                    self.enemies.remove(enemy)
                return enemy.get_changes()

            # если мы не включаем для enemy AI, то они будут двигаться рандомно, если включаем,
            # то будет обратный запрос к ai-service для инференса что делает медленнее обучение
            # и требует настроенной модели для enemy
            if enemy.ai and enemy.can_handle_ai_action():
                self._handle_ai_action(entity=enemy, is_cooperative=False)

            enemy.update(delta_time=delta_time)
            return enemy.get_changes()

        except Exception as e:
            logger.error(f"Error updating enemy {enemy.id}: {e}", exc_info=True)

    def update_weapon(self, weapon: Weapon, delta_time: float) -> WeaponUpdate | None:
        """Обновить оружие"""
        try:
            weapon.update(delta_time=delta_time, handle_weapon_explosion=self.handle_weapon_explosion)
            if weapon.is_exploded():
                #здесь оружие взорвалось и взрыв завершен
                self.weapons.pop(weapon.id)
                return weapon.get_changes()
            return weapon.get_changes()

        except Exception as e:
            logger.error(f"Error updating weapon {weapon.id}: {e}", exc_info=True)

    def handle_weapon_explosion(self, weapon: Weapon) -> None:
        """Обработать взрыв бомбы"""
        try:
            #если есть разрушенные блоки, то начисляем очки и генерируем бонусы
            for x, y in weapon.get_destroyed_blocks():
                # Начисляем очки команде владельца бомбы
                self.team_service.add_score_to_player_team(weapon.owner_id, self.settings.block_destroy_score)
                # Шанс появления усиления
                if random.random() < self.settings.powerup_drop_chance:
                    self.spawn_power_up(x=x * self.settings.cell_size , y=y * self.settings.cell_size)

            # Проверка коллизии с игроками
            for player in list(self.players.values()):
                if not player.invulnerable and self.check_explosion_collision(weapon=weapon, entity=player):
                    self.handle_player_hit(player=player, attacker_id=weapon.owner_id)

            # Проверка коллизии с врагами
            if self.settings.enable_enemies:
                for enemy in list(self.enemies):
                    if not enemy.destroyed and not enemy.invulnerable and self.check_explosion_collision(weapon=weapon, entity=enemy):
                        self.handle_enemy_hit(enemy=enemy, attacker_id=weapon.owner_id)

            # Проверка коллизии с другим оружием (цепная реакция)
            for other_weapon in self.weapons.values():
                if not other_weapon.activated:
                    if self.check_explosion_collision(weapon=weapon, entity=other_weapon):
                        other_weapon.activate(handle_weapon_explosion=self.handle_weapon_explosion)

        except Exception as e:
            logger.error(f"Error handling bomb explosion: {e}", exc_info=True)


    def setup_teams(self) -> None:
        """Настроить команды для режима прохождения - команды уже настроены в TeamService"""
        logger.info("Campaign mode: team setup completed via TeamService")

    def is_game_over(self) -> bool:
        """Игра заканчивается когда все игроки мертвы, все враги убиты или истекло время"""
        # Проверяем есть ли живые игроки
        alive_players = [p for p in self.players.values() if p.lives > 0]
        if not alive_players:
            self.game_over = True
            return True
        
        # Проверяем завершение уровня (все враги убиты)
        if self.settings.enable_enemies and len(self.enemies) == 0:
            return True

        # Если таймер активен и истёк — игрок проиграл (не успел уничтожить всех врагов)
        if self.settings.time_limit and self.settings.time_limit > 0 and self.time_remaining <= 0:
            self.game_over = True
            logger.info("Campaign mode: Time expired — player loses")
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
            elif self.settings.time_limit and self.settings.time_limit > 0 and self.time_remaining <= 0:
                # Время истекло — поражение (не успел уничтожить всех врагов)
                self.game_over = True
                for player in self.players.values():
                    self.team_service.add_score_to_player_team(
                        player_id=player.id,
                        points=self.settings.game_over_score
                    )
                logger.info("Campaign mode: Time expired - game over (defeat)")
            elif self.settings.enable_enemies and len(self.enemies) == 0:
                # Уровень завершен - переход на следующий уровень
                await self._level_complete()
                # Сбрасываем таймер на новый уровень
                self.time_remaining = float(self.settings.time_limit or 0)
                logger.info(f"Campaign mode: Level {self.level} completed")
            
        except Exception as e:
            logger.error(f"Error handling campaign game over: {e}", exc_info=True)
            self.game_over = True
    
    async def _level_complete(self) -> None:
        """Обработать завершение уровня"""
        try:
            self.level += 1
            
            # Начисляем очки команде за завершение уровня
            # В кампании все игроки в одной команде, начисляем очки первому игроку (команде)
            if self.players:
                for player in self.players.values():
                    self.team_service.add_score_to_player_team(
                        player_id=player.id,
                        points=self.settings.level_complete_score
                    )

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