import random

from enum import IntEnum
import numpy as np


class CellType(IntEnum):
    """Типы ячеек на карте"""
    EMPTY = 0
    SOLID_WALL = 1
    BREAKABLE_BLOCK = 2

class Map:
    def __init__(self, width: int, height: int):
        self.width: int = width
        self.height: int = height
        # Initialize grid with empty cells using numpy array
        self.grid: np.ndarray = np.zeros((height, width), dtype=np.int8)
        # Для отслеживания изменений на карте
        self.changed_cells: list[dict[str, int]] = []
    
    def generate_map(self) -> None:
        """Генерирует новую карту со стенами и разрушаемыми блоками"""
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
        for y in range(self.height):
            for x in range(self.width):
                if blocks_mask[y, x] and not self.is_player_start_area(x, y):
                    self.grid[y, x] = CellType.BREAKABLE_BLOCK
        
        # Сбрасываем список изменений при генерации новой карты
        self.changed_cells = []
    
    def is_player_start_area(self, x: int, y: int) -> bool:
        """Check if position is in a player starting area (corners)"""
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
    
    def get_cell_type(self, x: int, y: int) -> CellType:
        """Получает тип ячейки по указанным координатам"""
        # Проверка границ
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return CellType.SOLID_WALL  # За пределами карты считается твердой стеной
        
        return CellType(self.grid[y, x])
    
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
        # Проверка границ
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
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
            
    def get_map(self) -> dict:
        """Получает данные карты

        Returns:
            Словарь с данными карты, содержащий:
            - grid: массив numpy с полной картой
        """
        return {
            'grid': self.grid.tolist()
        }
        
    def clear_changes(self) -> None:
        """Очищает список отслеживаемых изменений"""
        self.changed_cells = []
        
    def get_changes(self) -> list[dict[str, int]]:
        """Возвращает список изменённых ячеек и очищает его"""
        changes = self.changed_cells.copy()
        self.clear_changes()
        return changes