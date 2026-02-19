import asyncio
import random
import time
from collections import defaultdict

import math
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any

from .team_service import TeamService
from .ai_inference_service import AIInferenceService
from .ai_action_mapper import action_to_inputs, action_to_direction
from .ai_observation import build_observation
from ..entities import Entity
from ..entities.map import Map
from ..entities.player import Player, UnitType, PlayerUpdate
from ..entities.enemy import Enemy, EnemyUpdate
from ..entities.weapon import Weapon, WeaponType, WeaponUpdate, WeaponAction
from ..entities.bomb import Bomb
from ..entities.bullet import Bullet
from ..entities.mine import Mine
from ..entities.power_up import PowerUp, PowerUpType, PowerUpUpdate
from ..models.game_models import GameSettings
from ..services.map_service import MapService
from ..models.map_models import MapState, PlayerState, EnemyState, WeaponState, PowerUpState, MapData, MapUpdate

logger = logging.getLogger(__name__)


class GameModeService(ABC):
    """Базовый класс для игровых режимов с общей логикой"""
    
    def __init__(
        self,
        game_settings: GameSettings,
        map_service: MapService,
        team_service: TeamService = None,
        ai_inference_service: AIInferenceService | None = None,
    ):
        self.settings: GameSettings = game_settings
        self.map_service: MapService = map_service
        self.team_service = team_service  # TeamService injection
        self.ai_inference_service: AIInferenceService | None = ai_inference_service
        
        # Состояние игры
        self.players: Dict[str, Player] = {}
        self.enemies: List[Enemy] = []
        self.weapons: Dict[str, Weapon] = {}
        self.power_ups: Dict[str, PowerUp] = {}
        self.map: Optional[Map] = None
        self.level: int = 1
        self.game_over: bool = False
        self.last_update_time: float = time.time()
        self._ai_pending_tasks: dict[str, asyncio.Task] = {}
        # Обратный отсчёт времени игры (0 = таймер отключён)
        self.time_remaining: float = float(self.settings.time_limit or 0)
    
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

            if not self.map:
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
    
    def add_player(self, player: Player) -> bool:
        """Добавить игрока в игру"""
        try:
            max_players = self.settings.max_players
            if len(self.players) >= max_players:
                logger.debug(f"Cannot add player {player.id}: maximum number of players reached ({max_players})")
                return False
            
            # Получаем доступные позиции спавна
            # Если разрешен спавн на пустых клетках, включаем их в список доступных позиций
            include_empty = self.settings.allow_spawn_on_empty_cells
            spawn_positions = self.map.get_player_spawn_positions(include_empty_cells=include_empty)
            
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
            
            # Найдем свободную позицию
            used_positions = set()
            for existing_player in self.players.values():
                player_grid_x = int(existing_player.x / self.settings.cell_size)
                player_grid_y = int(existing_player.y / self.settings.cell_size)
                used_positions.add((player_grid_x, player_grid_y))
            
            available_positions = [pos for pos in spawn_positions if pos not in used_positions]
            
            if not available_positions:
                logger.debug(f"Cannot add player {player.id}: no available spawn positions")
                return False
            
            # Назначаем позицию (рандомно или первую доступную в зависимости от настройки)
            if self.settings.randomize_spawn_assignment:
                x, y = random.choice(available_positions)
            else:
                x, y = available_positions[0]
            #TODO вынести логику рассчета относительных координат в саму карту,
            # карта должна заниматься рассчетом относительных коодринат, чтобы вне оьекта карты небыло
            # абсолютных координат в формате хранения ячеек и относительных с перерасчетом на размер ячейки для отображения
            player.x = x * self.settings.cell_size
            player.y = y * self.settings.cell_size
            
            # Назначаем цвет
            player_idx = len(self.players)
            if player_idx < len(player.COLORS):
                player.color = player.COLORS[player_idx]
                
            # Устанавливаем настройки игрока
            player.lives = self.settings.player_start_lives
            player.speed = self.settings.player_default_speed
            
            self.players[player.id] = player
            logger.info(f"Player {player.id} added at position ({x}, {y}) with color {player.color}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding player {player.id}: {e}", exc_info=True)
            return False

    def update_player_connection_status(self, player_id: str, connected: bool):
        player = self.get_player(player_id=player_id)
        if player:
            player.update_connection_status(connected=connected)


    def remove_player(self, player_id: str) -> bool:
        """Удалить игрока из игры"""
        try:
            if player_id in self.players:
                # Удаление из команд теперь обрабатывается TeamService
                logger.info(f"Player {player_id} removed from game")
                del self.players[player_id]
                return True
            else:
                logger.debug(f"Player {player_id} not found, cannot remove")
                return False
        except Exception as e:
            logger.error(f"Error removing player {player_id}: {e}", exc_info=True)
            return False
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Получить игрока по ID"""
        try:
            player = self.players.get(player_id)
            if player is None:
                logger.debug(f"Player {player_id} not found")
            return player
        except Exception as e:
            logger.error(f"Error getting player {player_id}: {e}", exc_info=True)
            return None
    
    async def update(self, *, delta_time: float | None = None) -> dict:
        """Обновить состояние игры и вернуть новое состояние"""
        try:
            # Вычисляем delta time
            current_time: float = time.time()
            if delta_time is None:
                delta_time = current_time - self.last_update_time
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


    def _cancel_ai_task(self, entity_id: str):
        task = self._ai_pending_tasks.pop(entity_id, None)
        if task and not task.done():
            task.cancel()

    def _handle_ai_action(self, *, entity: Entity, is_cooperative: bool = False):
        entity_id = entity.id
        is_player = isinstance(entity, Player)

        if entity_id in self._ai_pending_tasks:
            task = self._ai_pending_tasks[entity_id]
            if task.done():
                del self._ai_pending_tasks[entity_id]
                try:
                    action = task.result()
                except Exception:
                    action = None

                if action is not None:
                    entity.ai_last_action_time = time.time()
                    logger.debug(
                        f"Applying AI action={action} to entity={entity_id} "
                        f"(is_cooperative={is_cooperative}), current pos=({entity.x:.1f}, {entity.y:.1f})"
                    )
                    if is_player:
                        if action == 5:
                            si_placed_weapon = self.place_weapon(player=entity, weapon_action=WeaponAction.PLACEWEAPON1)
                            entity.set_inputs(inputs=action_to_inputs(action=0))
                        else:
                            entity.set_inputs(inputs=action_to_inputs(action=action))
                        #TODO Доработать под 2 других действия активировать 1 weapon и применить 2 weapon после того как они будут вообще имплементированы
                    else:
                        entity.direction = action_to_direction(action=action, current=entity.direction)
                        entity.move_timer = 0
                        logger.debug(
                            f"Enemy {entity_id} direction set to {entity.direction}, "
                            f"target cells reset"
                        )
            return

        enemies_positions: list[tuple[float, float]] = [
            (e.x, e.y) for e in self.enemies if not e.is_alive() and e.id != entity_id
        ]
        if not is_cooperative:
            enemies_positions.extend(
                (p.x, p.y) for p in self.players.values() if p.is_alive() and p.id != entity_id
            )
        weapons_positions: list[tuple[float, float]] = [
            (w.x, w.y) for w in self.weapons.values()
        ]
        power_ups_positions: list[tuple[float, float]] = [
            (p.x, p.y) for p in self.power_ups.values()
        ]
        if is_player:
            active_bombs: int = sum(1 for w in self.weapons.values() if w.owner_id == entity_id)
            max_bombs: int = entity.primary_weapon_max_count
            bomb_power: int = entity.primary_weapon_power
            max_lives_val: int = self.settings.player_max_lives
            entity_speed: float = entity.speed
        else:
            active_bombs = 0
            max_bombs = 0
            bomb_power = 0
            max_lives_val = max(1, entity.lives)
            entity_speed = entity.speed

        closest_dist: float = self.get_closest_enemy_distance(
            px=entity.x,
            py=entity.y,
        )

        obs_data = build_observation(
            map_grid=self.map.grid, map_width=self.map.width, map_height=self.map.height,
            cell_size=self.settings.cell_size,
            entity_x=entity.x, entity_y=entity.y,
            lives=entity.lives,
            max_lives=max_lives_val,
            enemy_count=len(self.enemies),
            max_enemies=self.map_service.enemy_count + (len(self.players) - 1),
            bombs_left=max(0, max_bombs - active_bombs),
            max_bombs=max_bombs,
            bomb_power=bomb_power,
            max_bomb_power=self.settings.max_bomb_power,
            is_invulnerable=entity.invulnerable,
            speed=entity_speed,
            max_speed=self.settings.player_max_speed,
            time_left=self.time_remaining,
            time_limit=float(self.settings.time_limit or 0),
            enemies_positions=enemies_positions,
            weapons_positions=weapons_positions,
            power_ups_positions=power_ups_positions,
            closest_enemy=closest_dist
        )
        # Use game_id as session_id to track episodes per game
        # This allows LSTM states to be reset when a new game starts
        game_id: str | None = getattr(self.settings, 'game_id', None)
        logger.debug(
            f"Requesting AI inference for entity={entity_id}, "
            f"pos=({entity.x:.1f}, {entity.y:.1f}), "
            f"direction={entity.direction}, "
            f"target_cell=({entity.ai_target_cell_x}, {entity.ai_target_cell_y}), "
            f"session={game_id}"
        )
        task = asyncio.create_task(
            self.ai_inference_service.maybe_infer_action(
                session_id=game_id,
                entity_id=entity_id,
                grid_values=obs_data.grid_values,
                stats_values=obs_data.stats_values,
            )
        )
        self._ai_pending_tasks[entity_id] = task

    def get_closest_enemy_distance(
        self,
        *,
        px: float,
        py: float,
    ) -> float:
        min_dist: float = 9999.0
        for e in self.enemies:
            if e.destroyed:
                continue
            dist: float = math.hypot(e.x - px, e.y - py)
            if dist < min_dist:
                min_dist = dist
        return min_dist

    def update_player(self, player: Player, delta_time: float) -> PlayerUpdate | None:
        """Обновить одного игрока"""
        try:
            if not player.is_alive():
                #TODO тут может нужно удалять игрока из списка, но не просто так, иначе в общем счете его не будет наверное
                self.players.pop(player.id)
                return player.get_changes()

            if player.ai and player.can_handle_ai_action():
                self._handle_ai_action(entity=player, is_cooperative=False)

            player.update(delta_time=delta_time)

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
                        self.handle_player_hit(player=player)
            return player.get_changes()
                        
        except Exception as e:
            logger.error(f"Error updating player {player.id}: {e}", exc_info=True)

    def update_enemy(self, enemy: Enemy, delta_time: float) -> EnemyUpdate | None:
        """Обновить одного врага"""
        try:
            if enemy.destroyed:
                self._cancel_ai_task(enemy.id)
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= self.settings.destroy_animation_time:
                    self.enemies.remove(enemy)
                return enemy.get_changes()

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


    def place_weapon(self, player: Player, weapon_action: WeaponAction) -> bool:
        """Применить оружие игрока"""
        try:
            #определяем доступно ли игроку выбранный тип оружия и получаем для него максимальное допустимое количество
            if weapon_action == WeaponAction.PLACEWEAPON1:
                weapon_type: WeaponType = player.primary_weapon
                weapon_max_count: int = player.primary_weapon_max_count
                weapon_power: int = player.primary_weapon_power
            elif weapon_action == WeaponAction.PLACEWEAPON2:
                weapon_type: WeaponType = player.primary_weapon
                weapon_max_count: int = player.secondary_weapon_max_count
                weapon_power: int = player.secondary_weapon_power
            else:
                return False

            # Подсчитываем активное оружие игрока определенного типа
            active_weapons = sum(1 for weapon in self.weapons.values() 
                               if weapon.owner_id == player.id and weapon.weapon_type == weapon_type)
            
            if active_weapons >= weapon_max_count:
                return False
            
            # Получаем позицию в сетке
            grid_x = round(player.x / self.settings.cell_size)
            grid_y = round(player.y / self.settings.cell_size)
            
            # weapon_x = grid_x * self.settings.cell_size
            # weapon_y = grid_y * self.settings.cell_size

            # Проверяем, нет ли weapon в этой позиции
            for weapon in self.weapons.values():
                weapon_grid_x = int((weapon.x + weapon.width/2) / self.settings.cell_size)
                weapon_grid_y = int((weapon.y + weapon.height/2) / self.settings.cell_size)

                if weapon_grid_x == grid_x and weapon_grid_y == grid_y:
                    return False

            if weapon_type == WeaponType.BOMB:
                weapon = Bomb(
                    x=grid_x * self.settings.cell_size,
                    y=grid_y * self.settings.cell_size,
                    size=self.settings.cell_size,
                    power=weapon_power,
                    owner_id=player.id,
                    map=self.map,
                    settings=self.settings,

                )
            elif weapon_type == WeaponType.BULLET:
                weapon = Bullet(
                    x=grid_x * self.settings.cell_size,
                    y=grid_y * self.settings.cell_size,
                    size=self.settings.cell_size,
                    direction=player.direction,
                    speed=weapon_power,
                    owner_id=player.id,
                    map=self.map,
                    settings=self.settings
                )
            elif weapon_type == WeaponType.MINE:
                weapon = Mine(
                    x=grid_x * self.settings.cell_size,
                    y=grid_y * self.settings.cell_size,
                    size=self.settings.cell_size,
                    owner_id=player.id,
                    map=self.map,
                    settings=self.settings
                )
            else:
                return False
            
            self.weapons[weapon.id] = weapon
            return True
            
        except Exception as e:
            logger.error(f"Error applying weapon for player {player.id}: {e}", exc_info=True)
            return False


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


    def check_entity_collision(self, entity1: Entity, entity2: Entity) -> bool:
        """Проверить коллизию двух сущностей"""
        try:
            return (entity1.x < entity2.x + entity2.width and
                    entity1.x + entity1.width > entity2.x and
                    entity1.y < entity2.y + entity2.height and
                    entity1.y + entity1.height > entity2.y)
        except Exception as e:
            logger.error(f"Error checking entity collision: {e}", exc_info=True)
            return False

    def check_explosion_collision(self, weapon: Weapon, entity: Entity) -> bool:
        """Проверить попадание сущности во взрыв"""
        try:
            entity_grid_x: int = int((entity.x + entity.width/2) / self.settings.cell_size)
            entity_grid_y: int = int((entity.y + entity.height/2) / self.settings.cell_size)
            
            for cell_x, cell_y in weapon.get_damage_area():
                if entity_grid_x == cell_x and entity_grid_y == cell_y:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking explosion collision: {e}", exc_info=True)
            return False


    def handle_player_hit(self, player: Player, attacker_id: str = None) -> None:
        """Обработать попадание в игрока"""
        try:
            player.set_hit()
            if player.destroyed:
                # Начисляем очки команде атакующего игрока
                if attacker_id:
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.player_destroy_score)
            
        except Exception as e:
            logger.error(f"Error handling player hit for player {player.id}: {e}", exc_info=True)


    def handle_enemy_hit(self, enemy: Enemy, attacker_id: str = None) -> None:
        """Обработать попадание во врага"""
        try:
            is_hit = enemy.set_hit()
            if is_hit:
                if enemy.destroyed:
                    # Начисляем очки команде атакующего игрока за уничтожение врага
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_destroy_score)
                    # Шанс появления бонуса
                    if random.random() < self.settings.enemy_powerup_drop_chance:
                        self.spawn_power_up(round(enemy.x), round(enemy.y))
                else:
                    # Начисляем очки команде атакующего игрока за попадение во врага
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_hit_score)

                    
        except Exception as e:
            logger.error(f"Error handling enemy hit: {e}", exc_info=True)
    
    def spawn_power_up(self, x: float, y: float) -> None:
        """Создать усиление в указанной позиции"""
        try:
            power_type: PowerUpType = random.choice(list(PowerUpType))
            power_up = PowerUp(
                x=x,
                y=y,
                size=self.settings.cell_size,
                power_type=power_type,
                map=self.map,
                settings=self.settings
            )
            self.power_ups[power_up.id] = power_up
        except Exception as e:
            logger.error(f"Error spawning power-up at ({x}, {y}): {e}", exc_info=True)
    
    def apply_power_up(self, player: Player, power_up: PowerUp) -> None:
        """Применить усиление к игроку"""
        try:
            power_up.apply_to_player(player)
            
            # Начисляем очки команде игрока
            self.team_service.add_score_to_player_team(player.id, self.settings.powerup_collect_score)
            self.power_ups.pop(power_up.id)
                
        except Exception as e:
            logger.error(f"Error applying power-up {power_up.type.name} to player {player.id}: {e}", exc_info=True)
    
    def _create_enemies(self, ai_enemies: bool = False) -> None:
        """Создать врагов для текущего уровня"""
        try:
            if not self.map:
                logger.warning("Cannot create enemies: no map available")
                return
            
            enemies_data = self.map_service.generate_enemies_for_level(self.map, self.level)
            self.enemies = []
            
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
                self.enemies.append(enemy)
            
            logger.info(f"Created {len(self.enemies)} enemies for level {self.level}")
            
        except Exception as e:
            logger.error(f"Error creating enemies for level {self.level}: {e}", exc_info=True)

    def is_alive(self):
        if time.time() - self.last_update_time <= self.settings.destroy_inactive_time:
            return True
        return False

    def is_active(self) -> bool:
        """Проверить активность игры"""
        try:
            return not self.game_over and len(self.players) > 0
        except Exception as e:
            logger.error(f"Error checking if game is active: {e}", exc_info=True)
            return False
    
    def get_state(self) -> MapState:
        """Получить полное состояние игры"""
        try:
            players_data: dict[str, PlayerState] = {}
            for player_id, player in self.players.items():
                players_data[player_id] = PlayerState(**player.get_changes(full_state=True))

            enemies_data: dict[str, EnemyState] = {}
            if self.settings.enable_enemies:
                for enemy in self.enemies:
                    enemies_data[enemy.id] = EnemyState(**enemy.get_changes(full_state=True))

            weapons_data: dict[str, WeaponState] = {}
            for weapon in self.weapons.values():
                weapons_data[weapon.id] = WeaponState(**weapon.get_changes(full_state=True))

            power_ups_data: dict[str, PowerUpState] = {}
            for power_up in self.power_ups.values():
                power_ups_data[power_up.id] = PowerUpState(**power_up.get_changes(full_state=True))

            map_data = self.map.get_map() if self.map else {'grid': None, 'width': 0, 'height': 0}

            return MapState(
                players=players_data,
                enemies=enemies_data,
                weapons=weapons_data,
                power_ups=power_ups_data,
                map=MapData(**map_data.model_dump()),
                level=self.level,
                teams=None
            )
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            return MapState(
                players={},
                enemies={},
                weapons={},
                power_ups={},
                map=MapData(grid=None, width=0, height=0),
                level=self.level,
                error=True,
                is_active=False,
                teams=None
            )
    
    # Абстрактные методы для переопределения в конкретных режимах
    @abstractmethod
    def is_game_over(self) -> bool:
        """Проверить условия окончания игры"""
        pass
    
    @abstractmethod
    async def handle_game_over(self) -> None:
        """Обработать окончание игры"""
        pass
    
    @abstractmethod
    def setup_teams(self) -> None:
        """Настроить команды для режима"""
        pass


