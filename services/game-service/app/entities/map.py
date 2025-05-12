import random
import logging
from enum import IntEnum
import numpy as np


logger = logging.getLogger(__name__)

class CellType(IntEnum):
    """Типы ячеек на карте"""
    EMPTY = 0
    SOLID_WALL = 1
    BREAKABLE_BLOCK = 2

class Map:
    def __init__(self, width: int, height: int):
        try:
            self.width: int = width
            self.height: int = height
            # Initialize grid with empty cells using numpy array
            self.grid: np.ndarray = np.zeros((height, width), dtype=np.int8)
            # Для отслеживания изменений на карте
            self.changed_cells: list[dict[str, int]] = []
            
            logger.info(f"Map initialized with dimensions {width}x{height}")
        except Exception as e:
            logger.error(f"Error initializing map: {e}", exc_info=True)
            raise
    
    def generate_map(self) -> None:
        """Генерирует новую карту со стенами и разрушаемыми блоками"""
        try:
            # Сброс сетки
            self.grid.fill(CellType.EMPTY)
            
            # Размещаем твердые стены по границам и в шахматном порядке
            self.grid[0, :] = CellType.SOLID_WALL  # Верхняя граница
            self.grid[-1, :] = CellType.SOLID_WALL  # Нижняя граница
            self.grid[:, 0] = CellType.SOLID_WALL  # Левая граница
            self.grid[:, -1] = CellType.SOLID_WALL  # Правая граница
            
            # Шахматный узор для внутренних стен
            self.grid[::2, ::2] = CellType.SOLID_WALL
            
            # Размещаем разрушаемые блоки случайным образом
            empty_mask = (self.grid == CellType.EMPTY)
            random_blocks = np.random.random(self.grid.shape) < 0.1
            blocks_mask = empty_mask & random_blocks
            
            # Исключаем стартовые зоны игроков
            breakable_blocks_count = 0
            for y in range(self.height):
                for x in range(self.width):
                    if blocks_mask[y, x] and not self.is_player_start_area(x, y):
                        self.grid[y, x] = CellType.BREAKABLE_BLOCK
                        breakable_blocks_count += 1
            
            # Сбрасываем список изменений при генерации новой карты
            self.changed_cells = []
            
            logger.info(f"Map generated with {breakable_blocks_count} breakable blocks")
        except Exception as e:
            logger.error(f"Error generating map: {e}", exc_info=True)
    
    def is_player_start_area(self, x: int, y: int) -> bool:
        """Check if position is in a player starting area (corners)"""
        try:
            # Top-left
            if x <= 2 and y <= 2:
                return True
            # Top-right
            if x >= self.width - 3 and y <= 2:
                return True
            # Bottom-left
            if x <= 2 and y >= self.height - 3:
                return True
            # Bottom-right
            if x >= self.width - 3 and y >= self.height - 3:
                return True
            return False
        except Exception as e:
            logger.error(f"Error checking player start area at ({x}, {y}): {e}", exc_info=True)
            return True  # Safely assume it's a player area in case of error
    
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
    
    def destroy_block(self, x: int, y: int) -> None:
        """Разрушает разрушаемый блок и отслеживает изменения"""
        try:
            # Проверка границ
            if x < 0 or x >= self.width or y < 0 or y >= self.height:
                logger.debug(f"Attempted to destroy block outside map boundaries at ({x}, {y})")
                return
            
            # Разрушаем только разрушаемые блоки
            if self.grid[y, x] == CellType.BREAKABLE_BLOCK:
                self.grid[y, x] = CellType.EMPTY
                # Отслеживаем изменения
                self.changed_cells.append(
                    {
                        'x': x,
                        'y': y,
                        'type': int(CellType.EMPTY)
                    }
                )
                logger.debug(f"Block destroyed at ({x}, {y})")
        except Exception as e:
            logger.error(f"Error destroying block at ({x}, {y}): {e}", exc_info=True)
            
    def get_map(self) -> dict:
        """Получает данные карты

        Returns:
            Словарь с данными карты, содержащий:
            - grid: массив numpy с полной картой
        """
        try:
            return {
                'grid': self.grid.tolist()
            }
        except Exception as e:
            logger.error(f"Error getting map data: {e}", exc_info=True)
            # Return empty grid in case of error
            return {'grid': []}
        
    def clear_changes(self) -> None:
        """Очищает список отслеживаемых изменений"""
        try:
            changes_count = len(self.changed_cells)
            self.changed_cells = []
            logger.debug(f"Cleared {changes_count} map changes")
        except Exception as e:
            logger.error(f"Error clearing map changes: {e}", exc_info=True)
            self.changed_cells = []
        
    def get_changes(self) -> list[dict[str, int]]:
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