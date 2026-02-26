import logging
import random
import time
from collections import defaultdict
from ..game_mode_service import GameModeService
from ..ai_inference_service import AIInferenceService
from ...entities import Enemy, Player, Entity, Map
from ...entities.enemy import EnemyUpdate, EnemyType
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


    def add_player(self, player: Entity) -> bool:
        """Добавить игрока в игру"""
        try:
            is_player: bool = isinstance(player, Player)

            if is_player:
                spawn_positions = self.map.get_player_spawn_positions(
                    include_empty_cells=self.settings.allow_spawn_on_empty_cells
                )
            else:
                spawn_positions = self.map.get_enemy_spawn_positions(
                    exclude_near_players=not self.settings.allow_enemies_near_players,
                    min_distance_from_players=self.settings.min_distance_from_players
                )

            if not spawn_positions:
                logger.warning("No player spawn positions found, using fallback positions")
                # Используем углы карты как запасной вариант
                spawn_positions = [
                    (1, 1),
                    (self.map.width - 2, 1),
                    (1, self.map.height - 2),
                    (self.map.width - 2, self.map.height - 2)
                ]

            # Рандомизируем spawn позиции если включена настройка (для шаблонов карт)
            if self.settings.randomize_spawn_positions:
                random.shuffle(spawn_positions)

            used_positions = set()
            # Найдем свободную позицию
            if is_player:
                for existing_player in self.players.values():
                    player_grid_x = int(existing_player.x / self.settings.cell_size)
                    player_grid_y = int(existing_player.y / self.settings.cell_size)
                    used_positions.add((player_grid_x, player_grid_y))
            else:
                for existing_enemies in self.enemies.values():
                    enemy_grid_x = int(existing_enemies.x / self.settings.cell_size)
                    enemy_grid_y = int(existing_enemies.y / self.settings.cell_size)
                    used_positions.add((enemy_grid_x, enemy_grid_y))

            available_positions = [pos for pos in spawn_positions if pos not in used_positions]

            if not available_positions:
                logger.debug(f"Cannot add player {player.id}: no available spawn positions")
                return False

            # Назначаем позицию (рандомно или первую доступную в зависимости от настройки)
            if self.settings.randomize_spawn_assignment:
                x, y = random.choice(available_positions)
            else:
                x, y = available_positions[0]

            player.x = x * self.settings.cell_size
            player.y = y * self.settings.cell_size

            if is_player:
                # Устанавливаем настройки игрока
                player.lives = self.settings.player_start_lives
                player.speed = self.settings.player_default_speed
                self.players[player.id] = player
            else:
                self.enemies[player.id] = player

            logger.info(f"Player {player.id} added at position ({x}, {y}) with color {player.color}")
            return True

        except Exception as e:
            logger.error(f"Error adding player {player.id}: {e}", exc_info=True)
            return False


    def _create_enemies(self, ai_enemies: bool = False) -> None:
        """Создать врагов для текущего уровня"""
        try:
            if not self.map:
                logger.warning("Cannot create enemies: no map available")
                return

            enemies_data = self.map_service.generate_enemies_for_level(self.map, self.level)
            self.enemies = {}

            for enemy_data in enemies_data:
                enemy = Enemy(
                    x=enemy_data['x'],
                    y=enemy_data['y'],
                    size=self.settings.cell_size,
                    speed=enemy_data['speed'],
                    enemy_type=enemy_data['type'],
                    map=self.map,
                    settings=self.settings,
                    ai=ai_enemies
                )
                self.enemies.update({enemy.id:enemy})

            logger.info(f"Created {len(self.enemies)} enemies for level {self.level}")

        except Exception as e:
            logger.error(f"Error creating enemies for level {self.level}: {e}", exc_info=True)


    async def initialize_map(self) -> None:
        """Инициализировать карту для игры"""
        try:
            if self.settings.map_template_id:
                self.map = await self.map_service.create_map_from_template(self.settings.map_template_id)
                if not self.map:
                    logger.warning(f"Failed to load map from chain {self.settings.map_template_id}, level {self.level}")

            elif self.settings.map_chain_id:
                # Загрузка из цепочки карт с учетом текущего уровня
                self.map = await self.map_service.create_map_from_chain(
                    chain_id=self.settings.map_chain_id,
                    level_index=self.level - 1
                )
                if not self.map:
                    logger.warning(f"Failed to load map from chain {self.settings.map_chain_id}, level {self.level}")
                    raise Exception({"error":"карта не была загружена из цепочки."})
            else:
                self.map = self.map_service.generate_random_map(
                    width=self.settings.default_map_width,
                    height=self.settings.default_map_height,
                    difficulty=self.level
                )

            # Создаем врагов если включены
            if self.settings.enable_enemies:
                self._create_enemies(ai_enemies=self.settings.enemy_ai_controlled)
        except Exception as e:
            logger.error(f"Error initializing map: {e}", exc_info=True)
            self.map = Map(self.settings.default_map_width, self.settings.default_map_height)


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
            # Обновляем врагов если включены
            if self.settings.enable_enemies:
                for enemy in list(self.enemies.values()):
                    result["enemies_update"].update({enemy.id: self.update_enemy(enemy=enemy, delta_time=delta_time)})

            # Обновляем игроков
            for player in list(self.players.values()):
                result["players_update"].update({player.id: self.update_player(player=player, delta_time=delta_time)})

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
                for enemy in self.enemies.values():
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
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= self.settings.destroy_animation_time:
                    self.enemies.pop(enemy.id)
                return enemy.get_changes()

            # если мы не включаем для enemy AI, то они будут двигаться рандомно, если включаем,
            # то будет обратный запрос к ai-service для инференса что делает медленнее обучение
            # и требует настроенной модели для enemy
            if enemy.ai and enemy.can_handle_ai_action():
                self._handle_ai_action(entity=enemy, is_cooperative=False)

            is_enemy_moved = enemy.update(delta_time=delta_time)
            self.team_service.add_score_to_player_team(
                player_id=enemy.id,
                points=self.settings.player_moved_score if is_enemy_moved else self.settings.played_did_not_moved_score
            )
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
                for enemy in list(self.enemies.values()):
                    if not enemy.destroyed and not enemy.invulnerable and self.check_explosion_collision(weapon=weapon, entity=enemy):
                        self.handle_enemy_hit(enemy=enemy, attacker_id=weapon.owner_id)

            # Проверка коллизии с другим оружием (цепная реакция)
            for other_weapon in self.weapons.values():
                if not other_weapon.activated:
                    if self.check_explosion_collision(weapon=weapon, entity=other_weapon):
                        other_weapon.activate(handle_weapon_explosion=self.handle_weapon_explosion)

        except Exception as e:
            logger.error(f"Error handling bomb explosion: {e}", exc_info=True)

    def handle_enemy_hit(self, enemy: Enemy, attacker_id: str = None) -> None:
        """Обработать попадание во врага"""
        try:
            is_hit = enemy.set_hit()
            if is_hit:
                if enemy.destroyed:
                    # Начисляем очки команде атакующего игрока за уничтожение врага
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_destroy_score)
                    # начисляем очки enemy для режиме его обучения
                    self.team_service.add_score_to_player_team(enemy.id, self.settings.killed_by_enemy_score)
                    # Шанс появления бонуса
                    if random.random() < self.settings.enemy_powerup_drop_chance:
                        self.spawn_power_up(round(enemy.x), round(enemy.y))
                else:
                    # Начисляем очки команде атакующего игрока за попадение во врага
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_hit_score)
                    # начисляем очки enemy для режиме его обучения
                    self.team_service.add_score_to_player_team(enemy.id, self.settings.hit_by_enemy_score)


        except Exception as e:
            logger.error(f"Error handling enemy hit: {e}", exc_info=True)

    def setup_teams(self) -> None:
        """Настроить команды для режима прохождения - команды уже настроены в TeamService"""
        logger.info("Campaign mode: team setup completed via TeamService")

    def is_game_over(self) -> bool:
        """Проверка Закончилась ли игра по условиям или нет, а дальше определяем победой или проигрышем
        Игра заканчивается когда все игроки мертвы, все враги убиты или истекло время"""
        # Проверяем есть ли живые игроки
        if self.settings.ai_training_player:
            alive_players = [p for p in self.players.values() if p.lives > 0]
            if not alive_players:
                self.game_over = True
                logger.info("Training ai mode: All players dead - game over")
                return True

            # Проверяем завершение уровня (все враги убиты)
            if len(self.players) == 1 and len(self.enemies) == 0:
                self.game_over = False
                return True

            # Если таймер активен и истёк — игрок проиграл (не успел уничтожить всех врагов)
            if self.settings.time_limit and self.settings.time_limit > 0 and self.time_remaining <= 0:
                self.game_over = True
                logger.info("Training ai mode: Time expired — player loses")
                for player in self.players.values():
                    self.team_service.add_score_to_player_team(
                        player_id=player.id,
                        points=self.settings.game_over_score
                    )
                return True
        else:
            #здесь мы обучаем enemy играть и определяем победу для него
            enemies_players = [p for p in self.enemies.values() if p.lives > 0]
            if not enemies_players:
                self.game_over = True
                logger.info("Training ai mode: All enemies dead - game over")
                return True

            # Проверяем завершение уровня (все враги убиты)
            if len(self.players) == 0 and len(self.enemies) == 1:
                self.game_over = False
                return True

            # Если таймер активен и истёк — игрок проиграл (не успел уничтожить всех врагов)
            if self.settings.time_limit and self.settings.time_limit > 0 and self.time_remaining <= 0:
                self.game_over = False
                for enemy in self.enemies.values():
                    self.team_service.add_score_to_player_team(
                        player_id=enemy.id,
                        points=self.settings.timeout_enemy_win_score
                    )
                logger.info("Training ai mode: Time expired — player loses")
                return True


        return False
    
    async def handle_game_over(self) -> None:
        """Обработать окончание игры в режиме прохождения"""
        try:
            # Уровень завершен - переход на следующий уровень
            await self._level_complete()
            # Сбрасываем таймер на новый уровень
            self.time_remaining = float(self.settings.time_limit or 0)
            logger.info(f"Training ai mode: Level {self.level} completed")
            
        except Exception as e:
            logger.error(f"Error handling Training ai game over: {e}", exc_info=True)
            self.game_over = True
    
    async def _level_complete(self) -> None:
        """Обработать завершение уровня"""
        try:
            self.level += 1

            # Начисляем очки команде за завершение уровня
            # В кампании все игроки в одной команде, начисляем очки первому игроку (команде)
            if self.settings.ai_training_player:
                if self.players:
                    for player in self.players.values():
                        self.team_service.add_score_to_player_team(
                            player_id=player.id,
                            points=self.settings.level_complete_score
                        )
            else:
                for enemy in self.enemies.values():
                    self.team_service.add_score_to_player_team(
                        player_id=enemy.id,
                        points=self.settings.level_complete_score
                    )

            # Сброс карты для следующего уровня
            await self.initialize_map()
            
            # Очистка оружия и усилений
            self.weapons = {}
            self.power_ups = {}
            
            # Сброс позиций игроков
            spawn_positions = self.map.get_player_spawn_positions(include_empty_cells=True)
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