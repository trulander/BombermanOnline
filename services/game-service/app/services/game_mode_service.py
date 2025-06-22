import random
import time
from collections import defaultdict

import math
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Any

from .team_service import TeamService
from ..entities import Entity
from ..entities.map import Map
from ..entities.player import Player, UnitType, PlayerUpdate
from ..entities.enemy import Enemy, EnemyUpdate
from ..entities.weapon import Weapon, WeaponType, WeaponUpdate
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
    
    async def update(self) -> dict:
        """Обновить состояние игры и вернуть новое состояние"""
        try:
            # Вычисляем delta time
            current_time: float = time.time()
            delta_time: float = current_time - self.last_update_time
            self.last_update_time = current_time

            # Пропускаем обновление если игра окончена
            if self.game_over:
                logger.debug("Game is over, skipping update")
                return {}

            result = {}
            # Обновляем игроков
            for player in list(self.players.values()):
                result["players_update"] = {player.id: self.update_player(player, delta_time)}
            
            # Обновляем врагов если включены
            if self.settings.enable_enemies:
                for enemy in list(self.enemies):
                    result["enemies_update"] = {enemy.id: self.update_enemy(enemy=enemy, delta_time=delta_time)}
            
            # Обновляем оружие
            for weapon in list(self.weapons.values()):
                result["weapons_update"] = {weapon.id: self.update_weapon(weapon, delta_time)}


            for power_up in self.power_ups.values():
                result["power_ups_update"] = {power_up: power_up.get_changes()}
            
            # Проверяем завершение игры
            if self.is_game_over():
                await self.handle_game_over()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in game update: {e}", exc_info=True)
            return {}
    
    def update_player(self, player: Player, delta_time: float) -> PlayerUpdate | None:
        """Обновить одного игрока"""
        try:
            if player.destroyed:
                #TODO тут может нужно удалять игрока из списка, но не просто так, иначе в общем счете его не будет наверное
                #self.players.pop(player.id)
                return None

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
                enemy.destroy_animation_timer += delta_time
                if enemy.destroy_animation_timer >= self.settings.destroy_animation_time:
                    self.enemies.remove(enemy)
                return None

            enemy.update(delta_time=delta_time)
            return enemy.get_changes()

        except Exception as e:
            logger.error(f"Error updating enemy {enemy.id}: {e}", exc_info=True)


    def update_weapon(self, weapon: Weapon, delta_time: float) -> WeaponUpdate | None:
        """Обновить оружие"""
        try:
            weapon.update(delta_time=delta_time, handle_weapon_explosion=self.handle_weapon_explosion)
            if weapon.activated and weapon.is_exploded():
                #здесь оружие взорвалось и взрыв завершен
                self.weapons.pop(weapon.id)
                return None
            return weapon.get_changes()

        except Exception as e:
            logger.error(f"Error updating weapon {weapon.id}: {e}", exc_info=True)


    def place_weapon(self, player: Player, weapon_type: WeaponType) -> bool:
        """Применить оружие игрока"""
        try:
            #определяем доступно ли игроку выбранный тип оружия и получаем для него максимальное допустимое количество
            if player.primary_weapon == weapon_type:
                weapon_max_count: int = player.primary_weapon_max_count
                weapon_power: int = player.primary_weapon_power
            elif player.secondary_weapon == weapon_type:
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
            grid_x = int((player.x + player.width/2) / self.settings.cell_size)
            grid_y = int((player.y + player.height/2) / self.settings.cell_size)
            
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
                    x=player.x,
                    y=player.y,
                    size=self.settings.cell_size,
                    power=weapon_power,
                    owner_id=player.id,
                    map=self.map,
                    settings=self.settings
                )
            elif weapon_type == WeaponType.BULLET:
                weapon = Bullet(
                    x=player.x,
                    y=player.y,
                    size=self.settings.cell_size,
                    direction=player.direction,
                    speed=weapon_power,
                    owner_id=player.id,
                    map=self.map,
                    settings=self.settings
                )
            elif weapon_type == WeaponType.MINE:
                weapon = Mine(
                    x=player.x,
                    y=player.y,
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
            #если есть разрушенные блоки, то начисляем очки о генерируем бонусы
            for x, y in weapon.get_destroyed_blocks():
                # Начисляем очки команде владельца бомбы
                self.team_service.add_score_to_player_team(weapon.owner_id, self.settings.block_destroy_score)
                # Шанс появления усиления
                if random.random() < self.settings.powerup_drop_chance:
                    self.spawn_power_up(x=x, y=y)

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
            enemy.set_hit()
            if enemy.destroyed:
                # Начисляем очки команде атакующего игрока
                if attacker_id:
                    self.team_service.add_score_to_player_team(attacker_id, self.settings.enemy_destroy_score)
                # Шанс появления бонуса
                if random.random() < self.settings.enemy_powerup_drop_chance:
                    self.spawn_power_up(enemy.x, enemy.y)
                    
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
                    x=enemy_data['x'],
                    y=enemy_data['y'],
                    size=self.settings.cell_size,
                    speed=enemy_data['speed'],
                    enemy_type=enemy_data['type'],
                    map=self.map,
                    settings=self.settings
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
    
    def get_state(self) -> MapState:
        """Получить полное состояние игры"""
        try:
            players_data: dict[str, PlayerState] = {}
            for player_id, player in self.players.items():
                players_data[player_id] = PlayerState(**player.get_changes(full_state=True))

            enemies_data: dict[str, EnemyState] = {}
            if self.settings.enable_enemies:
                for enemy in self.enemies:
                    enemies_data[enemy.id] = (EnemyState(**enemy.get_changes(full_state=True)))

            weapons_data: dict[str, WeaponState] = {}
            for weapon in self.weapons.values():
                weapons_data[weapon.id] = (WeaponState(**weapon.get_changes(full_state=True)))

            power_ups_data: dict[str, PowerUpState] = {}
            for power_up in self.power_ups.values():
                power_ups_data[power_up.id] = (PowerUpState(**power_up.get_changes(full_state=True)))

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
                enemies=[],
                weapons=[],
                power_ups=[],
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


