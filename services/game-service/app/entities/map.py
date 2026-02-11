import logging
from typing import List, Dict, Tuple
import numpy as np
from .cell_type import CellType
from ..models.map_models import MapData, MapUpdate

logger = logging.getLogger(__name__)


class Map:
    """Упрощенный класс карты без логики генерации"""
    
    def __init__(self, width: int, height: int):
        try:
            self.width: int = width
            self.height: int = height
            # Initialize grid with empty cells using numpy array
            self.grid: np.ndarray = np.zeros((height, width), dtype=np.int8)
            # Для отслеживания изменений на карте
            self.changed_cells: list[MapUpdate] = []
            
            logger.info(f"Map initialized with dimensions {width}x{height}")
        except Exception as e:
            logger.error(f"Error initializing map: {e}", exc_info=True)
            raise
    
    def load_from_template(self, grid_data: List[List[int]]) -> None:
        """Загрузить карту из шаблона"""
        try:
            if len(grid_data) != self.height or len(grid_data[0]) != self.width:
                raise ValueError(f"Grid data dimensions {len(grid_data)}x{len(grid_data[0])} don't match map dimensions {self.height}x{self.width}")
            
            # Конвертируем в numpy array
            self.grid = np.array(grid_data, dtype=np.int8)
            self.changed_cells = []
            
            logger.info(f"Map loaded from template: {self.width}x{self.height}")
        except Exception as e:
            logger.error(f"Error loading map from template: {e}", exc_info=True)
            raise
    
    def get_cell_type(self, x: int, y: int) -> CellType:
        """Получает тип ячейки по указанным координатам"""
        try:
            # Проверка границ
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                return CellType.SOLID_WALL  # За пределами карты считается твердой стеной
            
            return CellType(self.grid[y, x])
        except Exception as e:
            logger.error(f"Error getting cell type at ({x}, {y}): {e}", exc_info=True)
            return CellType.SOLID_WALL  # В случае ошибки считаем стеной для безопасности
    
    def set_cell_type(self, x: int, y: int, cell_type: CellType) -> None:
        """Устанавливает тип ячейки по указанным координатам"""
        try:
            # Проверка границ
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                logger.debug(f"Attempted to set cell type outside map boundaries at ({x}, {y})")
                return
            
            old_type = self.grid[y, x]
            self.grid[y, x] = int(cell_type)
            
            # Отслеживаем изменения если тип действительно изменился
            if old_type != int(cell_type):
                self.changed_cells.append(
                    MapUpdate(
                        x = x,
                        y = y,
                        type = cell_type
                    )
                )
                logger.debug(f"Cell type changed at ({x}, {y}): {CellType(old_type).name} -> {cell_type.name}")
            
        except Exception as e:
            logger.error(f"Error setting cell type at ({x}, {y}): {e}", exc_info=True)

    def get_available_direction(self, x: int, y: int) -> list[tuple[int, int]]:
        # offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)] # полная сетка с диагональными перемещениями
        offsets = [(-1, 0), (0, -1), (0, 1), (1, 0)]# только верх низ право лево
        neighbors = [(dx, dy) for dx, dy in offsets
                     if 0 <= x + dx < self.width and 0 <= y + dy < self.height
                     and self.grid[y + dy, x + dx] not in [CellType.SOLID_WALL.value, CellType.BREAKABLE_BLOCK.value]]
        return neighbors
    
    def is_wall(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка твердой стеной"""
        return self.get_cell_type(x, y) == CellType.SOLID_WALL
    
    def is_breakable_block(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка разрушаемым блоком"""
        return self.get_cell_type(x, y) == CellType.BREAKABLE_BLOCK
    
    def is_solid(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка твердой (стена или разрушаемый блок)"""
        cell_type = self.get_cell_type(x, y)
        return cell_type in (CellType.SOLID_WALL, CellType.BREAKABLE_BLOCK)
    
    def is_empty(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка пустой"""
        return self.get_cell_type(x, y) == CellType.EMPTY

    
    def destroy_block(self, x: int, y: int) -> bool:
        """Разрушает разрушаемый блок и отслеживает изменения"""
        try:
            # Проверка границ
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                logger.debug(f"Attempted to destroy block outside map boundaries at ({x}, {y})")
                return False
            
            # Разрушаем только разрушаемые блоки
            if self.grid[y, x] == CellType.BREAKABLE_BLOCK:
                self.set_cell_type(x, y, CellType.EMPTY)
                logger.debug(f"Block destroyed at ({x}, {y})")
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error destroying block at ({x}, {y}): {e}", exc_info=True)
            return False
    
    def get_empty_cells(
            self,
            exclude_near_players: bool = False,
            min_distance_from_players: int = 3
    ) -> List[Tuple[int, int]]:
        """Получить список пустых клеток на карте с возможностью исключения клеток рядом с игроками"""
        try:
            # Находим все пустые клетки с помощью numpy
            empty_mask = (self.grid == CellType.EMPTY)
            empty_coords = np.where(empty_mask)
            empty_cells = list(zip(empty_coords[1], empty_coords[0]))  # (x, y) координаты
            
            if exclude_near_players:
                # Получаем позиции спавна игроков
                player_spawns = self.get_player_spawn_positions()
                
                # Фильтруем клетки, исключая те, что близко к спавнам игроков
                filtered_cells = []
                for x, y in empty_cells:
                    is_far_enough = True
                    for px, py in player_spawns:
                        distance = abs(x - px) + abs(y - py)  # Манхэттенское расстояние
                        if distance < min_distance_from_players:
                            is_far_enough = False
                            break
                    if is_far_enough:
                        filtered_cells.append((x, y))
                
                empty_cells = filtered_cells
            
            logger.debug(f"Found {len(empty_cells)} empty cells (exclude_near_players={exclude_near_players})")
            return empty_cells
            
        except Exception as e:
            logger.error(f"Error getting empty cells: {e}", exc_info=True)
            return []
    
    def get_player_spawn_positions(self) -> List[Tuple[int, int]]:
        """Получить позиции спавна игроков с помощью numpy"""
        try:
            spawn_mask = (self.grid == CellType.PLAYER_SPAWN)
            spawn_coords = np.where(spawn_mask)
            spawn_positions = list(zip(spawn_coords[1], spawn_coords[0]))  # (x, y) координаты
            
            logger.debug(f"Found {len(spawn_positions)} player spawn positions")
            return spawn_positions
            
        except Exception as e:
            logger.error(f"Error getting player spawn positions: {e}", exc_info=True)
            return []
    
    def get_enemy_spawn_positions(
            self,
            exclude_near_players: bool = True,
            min_distance_from_players: int = 3
    ) -> List[Tuple[int, int]]:
        """Получить позиции спавна врагов с возможностью исключения позиций рядом с игроками"""
        try:
            spawn_mask = (self.grid == CellType.ENEMY_SPAWN)
            spawn_coords = np.where(spawn_mask)
            spawn_positions = list(zip(spawn_coords[1], spawn_coords[0]))  # (x, y) координаты
            
            if exclude_near_players:
                # Получаем позиции спавна игроков
                player_spawns = self.get_player_spawn_positions()
                
                # Фильтруем позиции спавна врагов
                filtered_positions = []
                for x, y in spawn_positions:
                    is_far_enough = True
                    for px, py in player_spawns:
                        distance = abs(x - px) + abs(y - py)  # Манхэттенское расстояние
                        if distance < min_distance_from_players:
                            is_far_enough = False
                            break
                    if is_far_enough:
                        filtered_positions.append((x, y))
                
                spawn_positions = filtered_positions
            
            logger.debug(f"Found {len(spawn_positions)} enemy spawn positions (exclude_near_players={exclude_near_players})")
            return spawn_positions
            
        except Exception as e:
            logger.error(f"Error getting enemy spawn positions: {e}", exc_info=True)
            return []

            
    def get_map(self) -> MapData:
        """Получает данные карты"""
        try:
            return MapData(
                grid = self.grid.tolist(),
                width = self.width,
                height = self.height
            )
        except Exception as e:
            logger.error(f"Error getting map data: {e}", exc_info=True)
            # Return empty grid in case of error
            return MapData(
                grid = None,
                width = self.width,
                height = self.height
            )
        
    def clear_changes(self) -> None:
        """Очищает список отслеживаемых изменений"""
        try:
            changes_count = len(self.changed_cells)
            self.changed_cells = []
            logger.debug(f"Cleared {changes_count} map changes")
        except Exception as e:
            logger.error(f"Error clearing map changes: {e}", exc_info=True)
            self.changed_cells = []
        
    def get_changes(self) -> list[MapUpdate]:
        """Возвращает список изменённых ячеек и очищает его"""
        try:
            changes = self.changed_cells.copy()
            changes_count = len(changes)
            self.clear_changes()
            logger.debug(f"Retrieved {changes_count} map changes")
            return changes
        except Exception as e:
            logger.error(f"Error getting map changes: {e}", exc_info=True)
            return []