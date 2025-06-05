import random
import time
import math
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any, Set

from .team_service import TeamService
from ..entities.map import Map
from ..entities.player import Player, UnitType
from ..entities.enemy import Enemy
from ..entities.weapon import Weapon, WeaponType
from ..entities.bomb import Bomb
from ..entities.bullet import Bullet
from ..entities.mine import Mine
from ..entities.power_up import PowerUp, PowerUpType
from ..entities.game_settings import GameSettings
from ..services.map_service import MapService

logger = logging.getLogger(__name__)


class GameModeService(ABC):
    """Базовый класс для игровых режимов с общей логикой"""
    
    def __init__(self, game_settings: GameSettings, map_service: MapService, team_service: TeamService=None):
        self.settings: GameSettings = game_settings
        self.map_service: MapService = map_service
        self.team_service = team_service  # TeamService injection
        
        # Состояние игры
        self.players: Dict[str, Player] = {}
        self.enemies: List[Enemy] = []
        self.weapons: Dict[str, Weapon] = {}
        self.power_ups: Dict[str, PowerUp] = {}
        self.map: Optional[Map] = None
        self.score: int = 0
        self.level: int = 1
        self.game_over: bool = False
        self.last_update_time: float = time.time()
    
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
                self._create_enemies()
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
            spawn_positions = self.map.get_player_spawn_positions()
            
            if not spawn_positions:
                logger.warning("No player spawn positions found, using fallback positions")
                spawn_positions = [
                    (1, 1),
                    (self.map.width - 2, 1),
                    (1, self.map.height - 2),
                    (self.map.width - 2, self.map.height - 2)
                ]
            
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
            
            # Назначаем позицию
            x, y = available_positions[0]
            player.x = x * self.settings.cell_size
            player.y = y * self.settings.cell_size
            
            # Назначаем цвет
            player_idx = len(self.players)
            if player_idx < len(player.COLORS):
                player.color = player.COLORS[player_idx]
                
            # Устанавливаем настройки игрока
            player.lives = self.settings.player_start_lives
            player.speed = self.settings.player_default_speed
            
            # Настраиваем оружие в зависимости от типа юнита
            if player.unit_type == UnitType.BOMBERMAN:
                player.max_weapons = self.settings.default_max_bombs
                player.weapon_power = self.settings.default_bomb_power
            
            self.players[player.id] = player
            logger.info(f"Player {player.id} added at position ({x}, {y}) with color {player.color}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding player {player.id}: {e}", exc_info=True)
            return False
    
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
    
    async def update(self) -> Dict[str, Any]:
        """Обновить состояние игры и вернуть новое состояние"""
        try:
            # Вычисляем delta time
            current_time: float = time.time()
            delta_time: float = current_time - self.last_update_time
            self.last_update_time = current_time
            
            # Пропускаем обновление если игра окончена
            if self.game_over:
                logger.debug("Game is over, skipping update")
                return self.get_state()
            
            # Обновляем игроков
            for player in list(self.players.values()):
                self.update_player(player, delta_time)
            
            # Обновляем врагов если включены
            if self.settings.enable_enemies:
                for enemy in list(self.enemies):
                    self.update_enemy(enemy, delta_time)
            
            # Обновляем оружие
            for weapon in list(self.weapons.values()):
                self.update_weapon(weapon, delta_time)
            
            # Проверяем завершение игры
            if self.is_game_over():
                await self.handle_game_over()
            
            return self.get_state()
            
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return self.get_state()
    
    def update_player(self, player: Player, delta_time: float) -> None:
        """Обновить одного игрока"""
        try:
            if player.lives <= 0:
                return

            player.update(delta_time=delta_time)
            
            # Обработка движения игрока
            dx: float = 0
            dy: float = 0
            if player.inputs.get('up'):
                dy -= player.speed
            if player.inputs.get('down'):
                dy += player.speed
            if player.inputs.get('left'):
                dx -= player.speed
            if player.inputs.get('right'):
                dx += player.speed
            
            # Нормализация диагонального движения
            if dx != 0 and dy != 0:
                normalize: float = 1 / math.sqrt(2)
                dx *= normalize
                dy *= normalize
            
            # Применяем delta time
            dx *= delta_time * 60
            dy *= delta_time * 60
            
            # Движение с проверкой коллизий (ось X)
            if dx != 0:
                new_x: float = player.x + dx
                if not self.check_collision(
                        x=new_x,
                        y=player.y,
                        width=player.width,
                        height=player.height,
                        entity=player,
                        ignore_entity=player
                ):
                    player.x = new_x
            
            # Движение с проверкой коллизий (ось Y)
            if dy != 0:
                new_y: float = player.y + dy
                if not self.check_collision(
                        x=player.x,
                        y=new_y,
                        width=player.width,
                        height=player.height,
                        entity=player,
                        ignore_entity=player
                ):
                    player.y = new_y
            
            # Проверка коллизии с усилениями
            for power_up in list(self.power_ups.values()):
                if self.check_entity_collision(player, power_up):
                    logger.info(f"Player {player.id} collected powerup {power_up.type.name}")
                    self.apply_power_up(player, power_up)
                    self.power_ups.pop(power_up.id)
            
            # Проверка коллизии с врагами
            if not player.invulnerable and self.settings.enable_enemies:
                for enemy in self.enemies:
                    if not enemy.destroyed and self.check_entity_collision(player, enemy):
                        logger.info(f"Player {player.id} hit by enemy {enemy.type.value}")
                        self.handle_player_hit(player)
                        
        except Exception as e:
            logger.error(f"Error updating player {player.id}: {e}", exc_info=True)

    def update_enemy(self, enemy: Enemy, delta_time: float) -> None:
        """Обновить одного врага"""
        try:
            if enemy.destroyed:
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= self.settings.enemy_destroy_animation_time:
                    self.enemies.remove(enemy)
                return

            enemy.update(delta_time=delta_time)
            
            # Обновление таймера движения
            enemy.move_timer += delta_time
            
            # Смена направления периодически или при столкновении со стеной
            if enemy.move_timer >= enemy.change_direction_interval:
                enemy.direction = enemy.get_random_direction()
                enemy.move_timer = 0
            
            # Вычисление новой позиции
            dx: float = enemy.direction[0] * enemy.speed * delta_time * 60
            dy: float = enemy.direction[1] * enemy.speed * delta_time * 60
            
            # Попытка движения в текущем направлении
            new_x: float = enemy.x + dx
            new_y: float = enemy.y + dy
            
            # Если есть коллизия, меняем направление
            if self.check_collision(
                    x=new_x,
                    y=new_y,
                    width=enemy.width,
                    height=enemy.height,
                    entity=enemy,
                    ignore_entity=None
            ):
                enemy.direction = enemy.get_random_direction()
            else:
                enemy.x = new_x
                enemy.y = new_y
                
        except Exception as e:
            logger.error(f"Error updating enemy {enemy.id}: {e}", exc_info=True)
    
    def update_weapon(self, weapon: Weapon, delta_time: float) -> None:
        """Обновить оружие"""
        try:
            weapon.update(delta_time)
            
            if isinstance(weapon, Bomb):
                if weapon.exploded:
                    if weapon.explosion_timer >= self.settings.bomb_explosion_duration:
                        self.weapons.pop(weapon.id)
                else:
                    if weapon.timer >= self.settings.bomb_timer:
                        self.handle_bomb_explosion(weapon)
            elif isinstance(weapon, Bullet):
                # Проверка коллизии пули с картой
                grid_x = int((weapon.x + weapon.width/2) / self.settings.cell_size)
                grid_y = int((weapon.y + weapon.height/2) / self.settings.cell_size)
                
                if self.map.is_solid(grid_x, grid_y) or weapon.hit_target:
                    weapon.activate()
                    self.weapons.pop(weapon.id)
                
                # Проверка попадания в цели
                for target_player in self.players.values():
                    if target_player.id != weapon.owner_id and self.check_entity_collision(weapon, target_player):
                        if not target_player.invulnerable:
                            self.handle_player_hit(target_player)
                        weapon.activate()
                        self.weapons.pop(weapon.id)
                        break
                
                for enemy in self.enemies:
                    if not enemy.destroyed and self.check_entity_collision(weapon, enemy):
                        self.handle_enemy_hit(enemy, weapon.owner_id)
                        weapon.activate()
                        self.weapons.pop(weapon.id)
                        break
            elif isinstance(weapon, Mine):
                # Проверка триггера мины
                if not weapon.triggered:
                    for player in self.players.values():
                        if player.id != weapon.owner_id and self.check_entity_collision(weapon, player):
                            weapon.trigger()
                            break
                
                if weapon.exploded:
                    # Проверка урона от мины
                    damage_area = weapon.get_damage_area()
                    for player in self.players.values():
                        if not player.invulnerable:
                            player_grid_x = int((player.x + player.width/2) / self.settings.cell_size)
                            player_grid_y = int((player.y + player.height/2) / self.settings.cell_size)
                            if (player_grid_x, player_grid_y) in damage_area:
                                self.handle_player_hit(player)
                    
                    # Убираем мину после взрыва
                    self.weapons.pop(weapon.id)
                    
        except Exception as e:
            logger.error(f"Error updating weapon {weapon.id}: {e}", exc_info=True)
    
    def apply_weapon(self, player: Player, weapon_type: WeaponType) -> bool:
        """Применить оружие игрока"""
        try:
            # Подсчитываем активное оружие игрока определенного типа
            active_weapons = sum(1 for weapon in self.weapons.values() 
                               if weapon.owner_id == player.id and weapon.weapon_type == weapon_type)
            
            if active_weapons >= player.max_weapons:
                return False
            
            # Получаем позицию в сетке
            grid_x = int((player.x + player.width/2) / self.settings.cell_size)
            grid_y = int((player.y + player.height/2) / self.settings.cell_size)
            
            weapon_x = grid_x * self.settings.cell_size
            weapon_y = grid_y * self.settings.cell_size
            
            if weapon_type == WeaponType.BOMB:
                # Проверяем, нет ли уже бомбы в этой позиции
                for weapon in self.weapons.values():
                    if isinstance(weapon, Bomb):
                        weapon_grid_x = int((weapon.x + weapon.width/2) / self.settings.cell_size)
                        weapon_grid_y = int((weapon.y + weapon.height/2) / self.settings.cell_size)
                        
                        if weapon_grid_x == grid_x and weapon_grid_y == grid_y:
                            return False
                
                weapon = Bomb(
                    x=weapon_x,
                    y=weapon_y,
                    size=self.settings.cell_size,
                    power=player.weapon_power,
                    owner_id=player.id
                )
            elif weapon_type == WeaponType.BULLET:
                weapon = Bullet(
                    x=player.x,
                    y=player.y,
                    size=self.settings.cell_size // 4,
                    direction=player.direction,
                    speed=self.settings.bullet_speed,
                    owner_id=player.id
                )
            elif weapon_type == WeaponType.MINE:
                weapon = Mine(
                    x=weapon_x,
                    y=weapon_y,
                    size=self.settings.cell_size,
                    owner_id=player.id
                )
            else:
                return False
            
            self.weapons[weapon.id] = weapon
            return True
            
        except Exception as e:
            logger.error(f"Error applying weapon for player {player.id}: {e}", exc_info=True)
            return False
    
    def handle_bomb_explosion(self, bomb: Bomb) -> None:
        """Обработать взрыв бомбы"""
        try:
            bomb.activate()
            bomb.explosion_cells = []
            
            # Получаем координаты бомбы в сетке
            grid_x: int = int((bomb.x + bomb.width/2) / self.settings.cell_size)
            grid_y: int = int((bomb.y + bomb.height/2) / self.settings.cell_size)
            
            # Добавляем центр взрыва
            bomb.explosion_cells.append((grid_x, grid_y))
            
            # Проверяем в каждом из четырех направлений
            directions: List[Tuple[int, int]] = [(0, -1), (1, 0), (0, 1), (-1, 0)]
            
            for dx, dy in directions:
                for i in range(1, bomb.power + 1):
                    check_x: int = grid_x + dx * i
                    check_y: int = grid_y + dy * i
                    
                    # Останавливаемся при попадании в стену
                    if self.map.is_wall(check_x, check_y):
                        break
                    
                    bomb.explosion_cells.append((check_x, check_y))
                    
                    # Если попали в разрушаемый блок, разрушаем его и останавливаем взрыв
                    if self.map.is_breakable_block(check_x, check_y):
                        if self.map.destroy_block(check_x, check_y):
                            # Начисляем очки команде владельца бомбы
                            if self.team_service:
                                self.team_service.add_score_to_player_team(bomb.owner_id, self.settings.block_destroy_score)
                            else:
                                self.score += self.settings.block_destroy_score
                        
                            # Шанс появления усиления
                            if random.random() < self.settings.powerup_drop_chance:
                                self.spawn_power_up(
                                    x=check_x * self.settings.cell_size,
                                    y=check_y * self.settings.cell_size
                                )
                        break
            
            # Проверка коллизии с игроками
            for player in list(self.players.values()):
                if not player.invulnerable and self.check_explosion_collision(bomb, player):
                    self.handle_player_hit(player)

            # Проверка коллизии с врагами
            if self.settings.enable_enemies:
                for enemy in list(self.enemies):
                    if not enemy.destroyed and not enemy.invulnerable and self.check_explosion_collision(bomb, enemy):
                        self.handle_enemy_hit(enemy, bomb.owner_id)

            # Проверка коллизии с другим оружием (цепная реакция)
            for other_weapon in self.weapons.values():
                if other_weapon != bomb and not other_weapon.activated:
                    if isinstance(other_weapon, Bomb) and self.check_explosion_collision(bomb, other_weapon):
                        self.handle_bomb_explosion(other_weapon)
                        
        except Exception as e:
            logger.error(f"Error handling bomb explosion: {e}", exc_info=True)
    
    def check_collision(
            self,
            x: float,
            y: float,
            width: int,
            height: int,
            entity: Any,
            ignore_entity=None,
    ) -> bool:
        """Проверить коллизию сущности"""
        try:
            # Вычисляем клетки сетки, с которыми пересекается сущность
            grid_left: int = int(x / self.settings.cell_size)
            grid_right: int = int((x + width - 1) / self.settings.cell_size)
            grid_top: int = int(y / self.settings.cell_size)
            grid_bottom: int = int((y + height - 1) / self.settings.cell_size)
            
            # Проверка коллизии с клетками карты
            for grid_y in range(grid_top, grid_bottom + 1):
                for grid_x in range(grid_left, grid_right + 1):
                    if self.map.is_solid(grid_x, grid_y):
                        return True
            
            # Проверка коллизии с оружием (только для бомб и мин)
            for weapon in self.weapons.values():
                if weapon != ignore_entity and weapon.owner_id != entity.id:
                    if isinstance(weapon, (Bomb, Mine)) and not weapon.activated:
                        weapon_grid_x: int = int((weapon.x + weapon.width/2) / self.settings.cell_size)
                        weapon_grid_y: int = int((weapon.y + weapon.height/2) / self.settings.cell_size)
                        
                        if (weapon_grid_x >= grid_left and weapon_grid_x <= grid_right and
                            weapon_grid_y >= grid_top and weapon_grid_y <= grid_bottom):
                            return True

            return False
            
        except Exception as e:
            logger.error(f"Error checking collision at ({x}, {y}): {e}", exc_info=True)
            return True

    def check_entity_collision(self, entity1: Any, entity2: Any) -> bool:
        """Проверить коллизию двух сущностей"""
        try:
            return (entity1.x < entity2.x + entity2.width and
                    entity1.x + entity1.width > entity2.x and
                    entity1.y < entity2.y + entity2.height and
                    entity1.y + entity1.height > entity2.y)
        except Exception as e:
            logger.error(f"Error checking entity collision: {e}", exc_info=True)
            return False

    def check_explosion_collision(self, bomb: Bomb, entity: Any) -> bool:
        """Проверить попадание сущности во взрыв"""
        try:
            entity_grid_x: int = int((entity.x + entity.width/2) / self.settings.cell_size)
            entity_grid_y: int = int((entity.y + entity.height/2) / self.settings.cell_size)
            
            for cell_x, cell_y in bomb.explosion_cells:
                if entity_grid_x == cell_x and entity_grid_y == cell_y:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking explosion collision: {e}", exc_info=True)
            return False
    
    def handle_player_hit(self, player: Player) -> None:
        """Обработать попадание в игрока"""
        try:
            if player.invulnerable:
                return
            
            player.lives -= 1
            
            if player.lives > 0:
                player.invulnerable = True
                player.invulnerable_timer = self.settings.player_invulnerable_time
            
        except Exception as e:
            logger.error(f"Error handling player hit for player {player.id}: {e}", exc_info=True)
    
    def handle_enemy_hit(self, enemy: Enemy, attacker_id: str = None) -> None:
        """Обработать попадание во врага"""
        try:
            if enemy.invulnerable:
                return

            enemy.lives -= 1
            
            if enemy.lives > 0:
                enemy.invulnerable = True
                enemy.invulnerable_timer = self.settings.enemy_invulnerable_time
            else:
                enemy.destroyed = True
                enemy.destroy_animation_timer = 0
                
                # Начисляем очки команде атакующего игрока
                if self.team_service and attacker_id:
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_destroy_score)
                else:
                    self.score += self.settings.enemy_destroy_score

                # Шанс появления усиления
                if random.random() < self.settings.enemy_powerup_drop_chance:
                    self.spawn_power_up(enemy.x, enemy.y)
                    
        except Exception as e:
            logger.error(f"Error handling enemy hit: {e}", exc_info=True)
    
    def spawn_power_up(self, x: float, y: float) -> None:
        """Создать усиление в указанной позиции"""
        try:
            power_type: PowerUpType = random.choice(list(PowerUpType))
            power_up = PowerUp(x, y, self.settings.cell_size, power_type)
            self.power_ups[power_up.id] = power_up
        except Exception as e:
            logger.error(f"Error spawning power-up at ({x}, {y}): {e}", exc_info=True)
    
    def apply_power_up(self, player: Player, power_up: PowerUp) -> None:
        """Применить усиление к игроку"""
        try:
            power_up.apply_to_player(player)
            
            # Начисляем очки команде игрока
            if self.team_service:
                self.team_service.add_score_to_player_team(player.id, self.settings.powerup_collect_score)
            else:
                self.score += self.settings.powerup_collect_score
                
        except Exception as e:
            logger.error(f"Error applying power-up {power_up.type.name} to player {player.id}: {e}", exc_info=True)
    
    def _create_enemies(self) -> None:
        """Создать врагов для текущего уровня"""
        try:
            if not self.map:
                logger.warning("Cannot create enemies: no map available")
                return
            
            enemies_data = self.map_service.generate_enemies_for_level(self.map, self.level)
            self.enemies = []
            
            for enemy_data in enemies_data:
                enemy = Enemy(
                    x=enemy_data['x'] * self.settings.cell_size,
                    y=enemy_data['y'] * self.settings.cell_size,
                    size=self.settings.cell_size,
                    speed=enemy_data['speed'],
                    enemy_type=enemy_data['type']
                )
                self.enemies.append(enemy)
            
            logger.info(f"Created {len(self.enemies)} enemies for level {self.level}")
            
        except Exception as e:
            logger.error(f"Error creating enemies for level {self.level}: {e}", exc_info=True)
    
    def is_active(self) -> bool:
        """Проверить активность игры"""
        try:
            return not self.game_over and len(self.players) > 0
        except Exception as e:
            logger.error(f"Error checking if game is active: {e}", exc_info=True)
            return False
    
    def get_state(self) -> Dict[str, Any]:
        """Получить полное состояние игры"""
        try:
            # Данные карты - только изменения
            map_data = {
                'width': self.map.width if self.map else self.settings.default_map_width,
                'height': self.map.height if self.map else self.settings.default_map_height,
                'changedCells': self.map.get_changes() if self.map else [],
                'cellSize': self.settings.cell_size
            }
            
            # Данные игроков
            players_data: Dict[str, Dict[str, Any]] = {}
            for player_id, player in self.players.items():
                players_data[player_id] = {
                    'x': player.x,
                    'y': player.y,
                    'width': player.width,
                    'height': player.height,
                    'lives': player.lives,
                    'maxWeapons': player.max_weapons,
                    'weaponPower': player.weapon_power,
                    'invulnerable': player.invulnerable,
                    'color': player.color,
                    'unitType': player.unit_type.value,
                    'teamId': player.team_id #self.team_service.get_player_team(player_id=player_id).id
                }

            # Данные врагов
            enemies_data: List[Dict[str, Any]] = []
            if self.settings.enable_enemies:
                for enemy in self.enemies:
                    enemies_data.append({
                        'x': enemy.x,
                        'y': enemy.y,
                        'width': enemy.width,
                        'height': enemy.height,
                        'type': enemy.type.value,
                        'lives': enemy.lives,
                        'invulnerable': enemy.invulnerable,
                        'destroyed': enemy.destroyed
                    })

            # Данные оружия
            weapons_data: List[Dict[str, Any]] = []
            for weapon in self.weapons.values():
                weapon_data = {
                    'x': weapon.x,
                    'y': weapon.y,
                    'width': weapon.width,
                    'height': weapon.height,
                    'type': weapon.weapon_type.value,
                    'activated': weapon.activated,
                    'ownerId': weapon.owner_id
                }
                
                if isinstance(weapon, Bomb):
                    explosion_cells: List[Dict[str, float]] = []
                    if weapon.exploded:
                        for x, y in weapon.explosion_cells:
                            explosion_cells.append({
                                'x': (x * self.settings.cell_size),
                                'y': (y * self.settings.cell_size)
                            })
                    weapon_data.update({
                        'exploded': weapon.exploded,
                        'explosionCells': explosion_cells
                    })
                elif isinstance(weapon, Bullet):
                    weapon_data.update({
                        'direction': weapon.direction,
                        'hitTarget': weapon.hit_target
                    })
                elif isinstance(weapon, Mine):
                    weapon_data.update({
                        'triggered': weapon.triggered,
                        'exploded': weapon.exploded
                    })
                
                weapons_data.append(weapon_data)

            # Данные усилений
            power_ups_data = [
                {
                    'x': power_up.x,
                    'y': power_up.y,
                    'width': power_up.width,
                    'height': power_up.height,
                    'type': power_up.type.value
                }
                for power_up in self.power_ups.values()
            ]

            state = {
                'players': players_data,
                'enemies': enemies_data,
                'weapons': weapons_data,
                'powerUps': power_ups_data,
                'map': map_data,
                'score': self.score,
                'level': self.level,
                'gameOver': self.game_over
            }
            
            return state
            
        except Exception as e:
            logger.error(f"Error getting game state: {e}", exc_info=True)
            # Возвращаем минимальное состояние при ошибке
            return {
                'error': True,
                'players': {},
                'enemies': [],
                'weapons': [],
                'powerUps': [],
                'map': {
                    'width': self.settings.default_map_width,
                    'height': self.settings.default_map_height,
                    'changedCells': [],
                    'cellSize': self.settings.cell_size
                },
                'score': self.score,
                'level': self.level,
                'gameOver': True
            }
    
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


