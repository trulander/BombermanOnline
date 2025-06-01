import logging
from typing import List, Dict
import numpy as np
from .cell_type import CellType

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
            self.changed_cells: List[Dict[str, int]] = []
            
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
                self.changed_cells.append({
                    'x': x,
                    'y': y,
                    'type': int(cell_type)
                })
                logger.debug(f"Cell type changed at ({x}, {y}): {CellType(old_type).name} -> {cell_type.name}")
            
        except Exception as e:
            logger.error(f"Error setting cell type at ({x}, {y}): {e}", exc_info=True)
    
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
    
    def is_player_spawn(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка точкой спавна игрока"""
        return self.get_cell_type(x, y) == CellType.PLAYER_SPAWN
    
    def is_enemy_spawn(self, x: int, y: int) -> bool:
        """Проверяет, является ли ячейка точкой спавна врага"""
        return self.get_cell_type(x, y) == CellType.ENEMY_SPAWN
    
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
            
    def get_map(self) -> Dict:
        """Получает данные карты"""
        try:
            return {
                'grid': self.grid.tolist(),
                'width': self.width,
                'height': self.height
            }
        except Exception as e:
            logger.error(f"Error getting map data: {e}", exc_info=True)
            # Return empty grid in case of error
            return {
                'grid': [],
                'width': self.width,
                'height': self.height
            }
        
    def clear_changes(self) -> None:
        """Очищает список отслеживаемых изменений"""
        try:
            changes_count = len(self.changed_cells)
            self.changed_cells = []
            logger.debug(f"Cleared {changes_count} map changes")
        except Exception as e:
            logger.error(f"Error clearing map changes: {e}", exc_info=True)
            self.changed_cells = []
        
    def get_changes(self) -> List[Dict[str, int]]:
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