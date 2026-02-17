import random
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from ..entities.cell_type import CellType
from ..entities.map import Map
from ..models.game_models import GameSettings
from ..entities.enemy import EnemyType
from ..models.map_models import MapTemplate
from ..repositories.map_repository import MapRepository
from ..config import settings

logger = logging.getLogger(__name__)


class MapService:
    """Сервис для управления картами, их генерацией и наполнением"""
    
    def __init__(self, map_repository: MapRepository, game_settings: GameSettings):
        self.map_repository = map_repository
        self.game_settings = game_settings
        self.enemy_count = 0
        
    async def create_map_from_template(self, template_id: str) -> Optional[Map]:
        """Создать карту на основе шаблона из базы данных"""
        try:
            template = await self.map_repository.get_map_template(template_id)
            if not template:
                logger.warning(f"Map template {template_id} not found")
                return None
            
            game_map = Map(width=template.width, height=template.height)
            game_map.load_from_template(template.grid_data)
            
            logger.info(f"Map created from template {template_id}: {template.width}x{template.height}")
            return game_map
            
        except Exception as e:
            logger.error(f"Error creating map from template {template_id}: {e}", exc_info=True)
            return None
    
    async def create_map_from_chain(self, chain_id: str, level_index: int = 0) -> Optional[Map]:
        """Создать карту из цепочки карт по индексу уровня"""
        try:
            chain = await self.map_repository.get_map_chain(chain_id)
            if not chain:
                logger.warning(f"Map chain {chain_id} not found")
                return None
                
            if level_index >= len(chain.map_ids):
                logger.warning(f"Level index {level_index} exceeds chain length {len(chain.map_ids)}")
                return None
                
            template_id = chain.map_ids[level_index]
            return await self.create_map_from_template(template_id)
            
        except Exception as e:
            logger.error(f"Error creating map from chain {chain_id}, level {level_index}: {e}", exc_info=True)
            return None
    
    async def create_map_from_group(self, group_id: str) -> Optional[Map]:
        """Создать случайную карту из группы карт"""
        try:
            group = await self.map_repository.get_map_group(group_id)
            if not group:
                logger.warning(f"Map group {group_id} not found")
                return None
                
            if not group.map_ids:
                logger.warning(f"Map group {group_id} has no maps")
                return None
                
            # Выбираем случайную карту из группы
            template_id = random.choice(group.map_ids)
            return await self.create_map_from_template(template_id)
            
        except Exception as e:
            logger.error(f"Error creating map from group {group_id}: {e}", exc_info=True)
            return None
    
    def generate_random_map(self, width: int, height: int, difficulty: int = 1) -> Map:
        """Генерировать случайную карту"""
        try:
            game_map = Map(width=width, height=height)
            
            # Заполняем границы твердыми стенами
            self._add_border_walls(game_map)
            
            # Добавляем внутренние стены
            if self.game_settings.enable_snake_walls:
                self._add_snake_walls(game_map)
            else:
                self._add_internal_walls(game_map)
            
            # Добавляем стартовые позиции игроков
            self._add_player_spawns(game_map)
            
            # Добавляем разрушаемые блоки (после спавнов игроков)
            self._add_breakable_blocks(game_map, difficulty)
            
            # Добавляем точки появления врагов
            self._add_enemy_spawns(game_map, difficulty)
            
            logger.info(f"Random map generated: {width}x{height}, difficulty={difficulty}")
            return game_map
            
        except Exception as e:
            logger.error(f"Error generating random map: {e}", exc_info=True)
            # Возвращаем базовую карту при ошибке
            return Map(width=width, height=height)
    
    def _add_border_walls(self, game_map: Map) -> None:
        """Добавить стены по границам карты"""
        try:
            # Верхняя и нижняя границы
            game_map.grid[0, :] = CellType.SOLID_WALL
            game_map.grid[-1, :] = CellType.SOLID_WALL
            
            # Левая и правая границы
            game_map.grid[:, 0] = CellType.SOLID_WALL
            game_map.grid[:, -1] = CellType.SOLID_WALL
            
        except Exception as e:
            logger.error(f"Error adding border walls: {e}", exc_info=True)
    
    def _add_internal_walls(self, game_map: Map) -> None:
        """Добавить внутренние стены в шахматном порядке"""
        try:
            # Шахматный узор для внутренних стен (начиная с четных координат)
            game_map.grid[2::2, 2::2] = CellType.SOLID_WALL
            
        except Exception as e:
            logger.error(f"Error adding internal walls: {e}", exc_info=True)
    
    def _add_snake_walls(self, game_map: Map) -> None:
        """Добавить стены змейкой с промежутками для спавна игроков"""
        try:
            # Генерируем стены змейкой через клетку
            for y in range(2, game_map.height - 2, 4):
                for x in range(2, game_map.width - 2, 2):
                    game_map.grid[y, x] = CellType.SOLID_WALL
                    
            for y in range(4, game_map.height - 2, 4):
                for x in range(1, game_map.width - 1, 2):
                    if x != 1 and x != game_map.width - 2:  # Оставляем места для спавна в углах
                        game_map.grid[y, x] = CellType.SOLID_WALL
            
        except Exception as e:
            logger.error(f"Error adding snake walls: {e}", exc_info=True)
    
    def _add_player_spawns(self, game_map: Map) -> None:
        """Добавить стартовые позиции игроков для случаев рандомной генерации карты"""
        try:
            # Получаем максимальное количество игроков из настроек
            max_players = self.game_settings.max_players
            
            # Получаем все пустые клетки
            empty_cells = game_map.get_empty_cells()
            
            if not empty_cells:
                logger.warning("No empty cells found for player spawns")
                return
            
            # Определяем приоритетные позиции (углы карты)
            corners = [
                (1, 1),                                # Верхний левый
                (game_map.width - 2, 1),               # Верхний правый
                (1, game_map.height - 2),              # Нижний левый
                (game_map.width - 2, game_map.height - 2)  # Нижний правый
            ]
            
            # Фильтруем углы, которые являются пустыми клетками
            available_corners = [corner for corner in corners if corner in empty_cells]
            
            # Добавляем дополнительные позиции для больших карт если нужно больше спавнов
            additional_positions = []
            if max_players > len(available_corners) and game_map.width >= 15 and game_map.height >= 15:
                additional_positions = [
                    (game_map.width // 2, 1),           # Верхний центр
                    (1, game_map.height // 2),          # Левый центр
                    (game_map.width - 2, game_map.height // 2),  # Правый центр
                    (game_map.width // 2, game_map.height - 2),  # Нижний центр
                ]
                # Фильтруем дополнительные позиции
                additional_positions = [pos for pos in additional_positions if pos in empty_cells]
            
            # Объединяем приоритетные позиции
            priority_positions = available_corners + additional_positions
            
            # Если все еще не хватает позиций, берем случайные пустые клетки
            if len(priority_positions) < max_players:
                remaining_cells = [cell for cell in empty_cells if cell not in priority_positions]
                if remaining_cells:
                    # Сортируем по расстоянию от центра карты для лучшего распределения
                    center_x, center_y = game_map.width // 2, game_map.height // 2
                    remaining_cells.sort(key=lambda pos: abs(pos[0] - center_x) + abs(pos[1] - center_y), reverse=True)
                    
                    needed = max_players - len(priority_positions)
                    priority_positions.extend(remaining_cells[:needed])
            
            # Рандомизируем позиции если включена настройка
            if self.game_settings.randomize_spawn_positions:
                random.shuffle(priority_positions)
            
            # Размещаем спавны игроков
            placed_spawns = 0
            for x, y in priority_positions[:max_players]:
                game_map.set_cell_type(x, y, CellType.PLAYER_SPAWN)
                placed_spawns += 1

            
            logger.debug(f"Added {placed_spawns} player spawn points for max_players={max_players}")
            
        except Exception as e:
            logger.error(f"Error adding player spawns: {e}", exc_info=True)
    
    def _add_breakable_blocks(self, game_map: Map, difficulty: int) -> None:
        """Добавить разрушаемые блоки"""
        try:
            # Базовая вероятность блоков
            base_probability = 0.1
            difficulty_multiplier = 1 + (difficulty - 1) * 0.05
            block_probability = min(base_probability * difficulty_multiplier, 0.3)
            
            # Получаем пустые клетки, исключая зоны рядом с игроками
            empty_cells = game_map.get_empty_cells(exclude_near_players=True, min_distance_from_players=3)
            
            # Размещаем блоки случайным образом
            for x, y in empty_cells:
                if random.random() < block_probability:
                    game_map.set_cell_type(x, y, CellType.BREAKABLE_BLOCK)
            
            logger.debug(f"Added breakable blocks with probability {block_probability:.2f}")
            
        except Exception as e:
            logger.error(f"Error adding breakable blocks: {e}", exc_info=True)
    
    def _add_enemy_spawns(self, game_map: Map, difficulty: int) -> None:
        """Добавить точки появления врагов"""
        try:
            # Получаем пустые клетки с учетом настроек расстояния от игроков
            min_distance = self.game_settings.min_distance_from_players
            allow_near_players = self.game_settings.allow_enemies_near_players
            
            empty_cells = game_map.get_empty_cells(
                exclude_near_players=not allow_near_players,
                min_distance_from_players=min_distance
            )
            
            # Количество точек спавна зависит от сложности и размера карты
            map_area = game_map.width * game_map.height
            base_spawn_count = max(3, map_area // 100)
            spawn_count = int(base_spawn_count * (1 + difficulty * 0.3))
            
            # Размещаем точки спавна врагов
            if empty_cells:
                spawn_positions = random.sample(
                    empty_cells, 
                    min(spawn_count, len(empty_cells))
                )
                
                for x, y in spawn_positions:
                    game_map.set_cell_type(x, y, CellType.ENEMY_SPAWN)
            
            logger.debug(f"Added {len(spawn_positions) if empty_cells else 0} enemy spawn points")
            
        except Exception as e:
            logger.error(f"Error adding enemy spawns: {e}", exc_info=True)
    
    def generate_enemies_for_level(self, game_map: Map, level: int) -> List[Dict[str, Any]]:
        """Генерировать врагов для уровня"""
        try:
            # Получаем позиции спавна врагов с учетом настроек
            min_distance = self.game_settings.min_distance_from_players
            allow_near_players = self.game_settings.allow_enemies_near_players
            
            enemy_spawns = game_map.get_enemy_spawn_positions(
                exclude_near_players=not allow_near_players,
                min_distance_from_players=min_distance
            )
            
            if not enemy_spawns:
                # Если нет специальных точек спавна, используем пустые клетки
                enemy_spawns = game_map.get_empty_cells(
                    exclude_near_players=not allow_near_players,
                    min_distance_from_players=min_distance
                )
            
            # Базовое количество врагов + увеличение по уровням
            base_enemy_count = 3
            level_multiplier = self.game_settings.enemy_count_multiplier
            self.enemy_count = int(base_enemy_count + level * level_multiplier)
            
            # Ограничиваем количество доступными позициями
            self.enemy_count = min(self.enemy_count, len(enemy_spawns))
            
            if self.enemy_count == 0:
                logger.warning("No valid enemy spawn positions found")
                return []
            
            # Выбираем случайные позиции
            chosen_positions = random.sample(enemy_spawns, self.enemy_count)
            
            # Генерируем врагов
            enemies_data = []
            enemy_types = list(EnemyType)
            
            for x, y in chosen_positions:
                enemy_type = random.choice(enemy_types)
                speed = 1.0 + random.random() * 0.5
                
                # Усложнение врагов на высоких уровнях
                if level > 5:
                    speed += (level - 5) * 0.1
                
                enemy_data = {
                    'x': x * self.game_settings.cell_size,
                    'y': y * self.game_settings.cell_size,
                    'type': enemy_type,
                    'speed': speed
                }
                enemies_data.append(enemy_data)
            
            logger.info(f"Generated {len(enemies_data)} enemies for level {level}")
            return enemies_data
            
        except Exception as e:
            logger.error(f"Error generating enemies for level {level}: {e}", exc_info=True)
            return [] 