import random
import logging
from typing import List, Tuple, Optional, Dict, Any
import numpy as np
from ..entities.cell_type import CellType
from ..entities.map import Map
from ..entities.game_settings import GameSettings
from ..entities.enemy import EnemyType
from ..models.map_models import MapTemplate
from ..repositories.map_repository import MapRepository

logger = logging.getLogger(__name__)


class MapService:
    """Сервис для управления картами, их генерацией и наполнением"""
    
    def __init__(self, map_repository: MapRepository, game_settings: GameSettings):
        self.map_repository = map_repository
        self.game_settings = game_settings
        
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
    
    def generate_random_map(self, width: int, height: int, difficulty: int = 1) -> Map:
        """Генерировать случайную карту"""
        try:
            game_map = Map(width=width, height=height)
            
            # Заполняем границы твердыми стенами
            self._add_border_walls(game_map)
            
            # Добавляем внутренние стены в шахматном порядке
            self._add_internal_walls(game_map)
            
            # Добавляем разрушаемые блоки
            self._add_breakable_blocks(game_map, difficulty)
            
            # Добавляем стартовые позиции игроков
            self._add_player_spawns(game_map)
            
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
        #TODO добавить возможность генерировать стены во круг змейкой, так чтобы можно было через 1 клетку стены размещать позицию для спавна игроков в некоторый режимах игры. Вынести параметр настройки игры для генерации такого типа стен.
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
    
    def _add_breakable_blocks(self, game_map: Map, difficulty: int) -> None:
        """Добавить разрушаемые блоки"""
        try:
            # Базовая вероятность блоков
            base_probability = 0.1
            difficulty_multiplier = 1 + (difficulty - 1) * 0.05
            block_probability = min(base_probability * difficulty_multiplier, 0.3)
            
            # Получаем пустые клетки
            empty_cells = self.get_empty_cells(game_map)
            
            # Размещаем блоки случайным образом
            for x, y in empty_cells:
                if random.random() < block_probability:
                    # Проверяем, что это не зона старта игроков
                    if not self._is_player_start_area(x, y, game_map.width, game_map.height):
                        game_map.grid[y, x] = CellType.BREAKABLE_BLOCK
            
            logger.debug(f"Added breakable blocks with probability {block_probability:.2f}")
            
        except Exception as e:
            logger.error(f"Error adding breakable blocks: {e}", exc_info=True)
    
    def _add_player_spawns(self, game_map: Map) -> None:
        """Добавить стартовые позиции игроков"""
        #TODO Этот метод должен быть переписан и использовать методы get_empty_cells
        try:
            # Базовые позиции в углах (совместимость с существующим кодом)
            spawn_positions = [
                (1, 1),                                # Верхний левый
                (game_map.width - 2, 1),               # Верхний правый
                (1, game_map.height - 2),              # Нижний левый
                (game_map.width - 2, game_map.height - 2)  # Нижний правый
            ]

            # Добавляем дополнительные позиции для больших карт
            if game_map.width >= 15 and game_map.height >= 15:
                additional_spawns = [
                    (game_map.width // 2, 1),           # Верхний центр
                    (1, game_map.height // 2),          # Левый центр
                    (game_map.width - 2, game_map.height // 2),  # Правый центр
                    (game_map.width // 2, game_map.height - 2),  # Нижний центр
                ]
                spawn_positions.extend(additional_spawns)

            # Размещаем позиции спавна
            placed_spawns = 0
            for x, y in spawn_positions:
                if (0 <= x < game_map.width and 0 <= y < game_map.height and
                    game_map.grid[y, x] == CellType.EMPTY):
                    game_map.grid[y, x] = CellType.PLAYER_SPAWN
                    placed_spawns += 1
                    
                    # Освобождаем область вокруг спавна
                    self._clear_spawn_area(game_map, x, y, radius=2)
            
            logger.debug(f"Added {placed_spawns} player spawn points")
            
        except Exception as e:
            logger.error(f"Error adding player spawns: {e}", exc_info=True)
    
    def _add_enemy_spawns(self, game_map: Map, difficulty: int) -> None:
        """Добавить точки появления врагов"""
        try:
            empty_cells = self.get_empty_cells(game_map)
            
            # Количество точек спавна зависит от сложности и размера карты
            map_area = game_map.width * game_map.height
            base_spawn_count = max(3, map_area // 100)
            spawn_count = int(base_spawn_count * (1 + difficulty * 0.3))
            
            # Фильтруем клетки - исключаем зоны рядом с игроками
            valid_cells = []
            for x, y in empty_cells:
                if not self._is_near_player_spawn(game_map, x, y, min_distance=4):
                    valid_cells.append((x, y))
            
            # Размещаем точки спавна врагов
            if valid_cells:
                spawn_positions = random.sample(
                    valid_cells, 
                    min(spawn_count, len(valid_cells))
                )
                
                for x, y in spawn_positions:
                    game_map.grid[y, x] = CellType.ENEMY_SPAWN
            
            logger.debug(f"Added {len(spawn_positions)} enemy spawn points")
            
        except Exception as e:
            logger.error(f"Error adding enemy spawns: {e}", exc_info=True)

    #TODO убрать этот ебаный метод отсюда, он должен быть в самой карте, карта может отфильтровать пустые яцейки так как там nympy массив, а не эта поганая логика которая тут реализована
    def get_empty_cells(self, game_map: Map) -> List[Tuple[int, int]]:
        """Получить список пустых клеток на карте"""
        try:
            empty_cells = []
            for y in range(game_map.height):
                for x in range(game_map.width):
                    if game_map.grid[y, x] == CellType.EMPTY:
                        empty_cells.append((x, y))
            
            logger.debug(f"Found {len(empty_cells)} empty cells")
            return empty_cells
            
        except Exception as e:
            logger.error(f"Error getting empty cells: {e}", exc_info=True)
            return []

    #TODO удрать этот ебучий метод отсюда, он должен быть в классе карты, вместо этой ебучей логики нужно использовать фильтрацию в карте так как там numpy array
    def get_player_spawn_positions(self, game_map: Map) -> List[Tuple[int, int]]:
        """Получить позиции спавна игроков"""
        try:
            spawn_positions = []
            for y in range(game_map.height):
                for x in range(game_map.width):
                    if game_map.grid[y, x] == CellType.PLAYER_SPAWN:
                        spawn_positions.append((x, y))
            
            logger.debug(f"Found {len(spawn_positions)} player spawn positions")
            return spawn_positions
            
        except Exception as e:
            logger.error(f"Error getting player spawn positions: {e}", exc_info=True)
            return []

    #TODO удрать этот ебучий метод отсюда, он должен быть в классе карты, вместо этой ебучей логики нужно использовать фильтрацию в карте так как там numpy array
    def get_enemy_spawn_positions(self, game_map: Map) -> List[Tuple[int, int]]:
        """Получить позиции спавна врагов"""
        try:
            spawn_positions = []
            for y in range(game_map.height):
                for x in range(game_map.width):
                    if game_map.grid[y, x] == CellType.ENEMY_SPAWN:
                        spawn_positions.append((x, y))
            
            logger.debug(f"Found {len(spawn_positions)} enemy spawn positions")
            return spawn_positions
            
        except Exception as e:
            logger.error(f"Error getting enemy spawn positions: {e}", exc_info=True)
            return []
    
    def generate_enemies_for_level(self, game_map: Map, level: int) -> List[Dict[str, Any]]:
        """Генерировать врагов для уровня"""
        try:
            enemy_spawns = self.get_enemy_spawn_positions(game_map)
            if not enemy_spawns:
                # Если нет специальных точек спавна, используем пустые клетки
                #TODO должен быть заменен на метод который возвращает пустые клетки с учетом позиций размещения игроков
                empty_cells = self.get_empty_cells(game_map)
                # Фильтруем клетки подальше от игроков
                enemy_spawns = [
                    (x, y) for x, y in empty_cells 
                    if not self._is_near_player_spawn(game_map, x, y, min_distance=3)
                ]
            
            # Базовое количество врагов + увеличение по уровням
            base_enemy_count = 3
            level_multiplier = self.game_settings.game_mode.enemy_count_multiplier
            enemy_count = int(base_enemy_count + level * level_multiplier)
            
            # Ограничиваем количество доступными позициями
            enemy_count = min(enemy_count, len(enemy_spawns))
            
            if enemy_count == 0:
                logger.warning("No valid enemy spawn positions found")
                return []
            
            # Выбираем случайные позиции
            chosen_positions = random.sample(enemy_spawns, enemy_count)
            
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
                    'x': x,
                    'y': y,
                    'type': enemy_type,
                    'speed': speed
                }
                enemies_data.append(enemy_data)
            
            logger.info(f"Generated {len(enemies_data)} enemies for level {level}")
            return enemies_data
            
        except Exception as e:
            logger.error(f"Error generating enemies for level {level}: {e}", exc_info=True)
            return []

    #TODO этот метод не нужен вообще, он повторяет логику метода который исключает из доступных для размещения разрушаемыз блоков позиции для спавна игроков
    def _is_player_start_area(self, x: int, y: int, width: int, height: int) -> bool:
        """Проверить, находится ли позиция в стартовой зоне игрока"""
        try:
            # Углы карты - традиционные зоны старта
            corner_size = 3
            
            # Верхний левый угол
            if x < corner_size and y < corner_size:
                return True
            # Верхний правый угол
            if x >= width - corner_size and y < corner_size:
                return True
            # Нижний левый угол
            if x < corner_size and y >= height - corner_size:
                return True
            # Нижний правый угол
            if x >= width - corner_size and y >= height - corner_size:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking player start area at ({x}, {y}): {e}", exc_info=True)
            return True  # В случае ошибки считаем зоной старта для безопасности

    #TODO перенести эту ебаную логику в метод get_enemy_spawn_positions и вместе с ним перенести в класс карты в и добавить в него новый параметр настройки игры в котором можно задавать разрешать появляться enemy рядом с игроками, или нет, по дефолту нельзя.
    def _is_near_player_spawn(self, game_map: Map, x: int, y: int, min_distance: int) -> bool:
        """Проверить, находится ли позиция рядом с точкой спавна игрока"""
        try:
            for sy in range(game_map.height):
                for sx in range(game_map.width):
                    if game_map.grid[sy, sx] == CellType.PLAYER_SPAWN:
                        distance = abs(x - sx) + abs(y - sy)  # Манхэттенское расстояние
                        if distance < min_distance:
                            return True
            return False
            
        except Exception as e:
            logger.error(f"Error checking proximity to player spawn at ({x}, {y}): {e}", exc_info=True)
            return True  # В случае ошибки считаем близко к спавну

    #TODO этого метода не должно существовать, эта логика должна быть реализована в классе карты в виде дополненного метода get_empty_cells с учетом позиций спавнов для игроков и использоваться и в _add_breakable_blocks и в _add_enemy_spawns и в generate_enemies_for_level так как используется подобная логика.
    def _clear_spawn_area(self, game_map: Map, center_x: int, center_y: int, radius: int) -> None:
        """Очистить область вокруг точки спавна"""
        try:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    x, y = center_x + dx, center_y + dy
                    if (0 <= x < game_map.width and 0 <= y < game_map.height):
                        # Очищаем только разрушаемые блоки, не затрагивая стены
                        if game_map.grid[y, x] == CellType.BREAKABLE_BLOCK:
                            game_map.grid[y, x] = CellType.EMPTY
                            
        except Exception as e:
            logger.error(f"Error clearing spawn area at ({center_x}, {center_y}): {e}", exc_info=True) 