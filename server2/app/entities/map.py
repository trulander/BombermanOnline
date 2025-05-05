import random

from enum import IntEnum
import numpy as np
from typing import Tuple

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
        random_blocks = np.random.random(self.grid.shape) < 0.4
        blocks_mask = empty_mask & random_blocks
        
        # Исключаем стартовые зоны игроков
        for y in range(self.height):
            for x in range(self.width):
                if blocks_mask[y, x] and not self.is_player_start_area(x, y):
                    self.grid[y, x] = CellType.BREAKABLE_BLOCK
    
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
        """Разрушает разрушаемый блок"""
        # Проверка границ
        if x < 0 or x >= self.width or y < 0 or y >= self.height:
            return
        
        # Разрушаем только разрушаемые блоки
        if self.grid[y, x] == CellType.BREAKABLE_BLOCK:
            self.grid[y, x] = CellType.EMPTY
            
    def get_map(self, player_x: float | None = None, player_y: float | None = None) -> dict:
        """Получает часть карты в указанных границах, центрированную относительно позиции игрока
        
        Args:
            player_x: X-координата игрока
            player_y: Y-координата игрока
            
        Returns:
            Словарь с данными карты, содержащий:
            - grid: массив numpy с частью карты в указанных границах
            - start: кортеж (x, y) начальной точки
            - end: кортеж (x, y) конечной точки
            - width: ширина видимой области
            - height: высота видимой области
            - view_offset: смещение видимой области относительно начала карты
        """
        # Если координаты игрока не переданы, возвращаем всю карту
        if player_x is None or player_y is None:
            return {
                'grid': self.grid.tolist(),
                'start': (0, 0),
                'end': (self.width, self.height),
                'width': self.width,
                'height': self.height,
                'view_offset': {'x': 0, 'y': 0}
            }
            
        # Преобразуем координаты игрока в координаты сетки
        cell_size = 40  # размер ячейки
        grid_x = int(player_x / cell_size)
        grid_y = int(player_y / cell_size)
        
        # Определяем размер видимой области (по 7 клеток в каждую сторону от игрока)
        view_radius = 7
        view_width = view_radius * 2 + 1
        view_height = view_radius * 2 + 1
        
        # Вычисляем начальные координаты видимой области
        start_x = max(0, min(self.width - view_width, grid_x - view_radius))
        start_y = max(0, min(self.height - view_height, grid_y - view_radius))
        
        # Вычисляем конечные координаты видимой области
        end_x = min(self.width, start_x + view_width)
        end_y = min(self.height, start_y + view_height)
        
        # Получаем срез карты
        grid_slice = self.grid[start_y:end_y, start_x:end_x].copy()
        
        # Вычисляем смещение видимой области относительно начала карты в пикселях
        view_offset_x = start_x * cell_size
        view_offset_y = start_y * cell_size
        
        # Формируем словарь с данными
        return {
            'grid': grid_slice.tolist(),
            'start': (start_x, start_y),
            'end': (end_x, end_y),
            'width': end_x - start_x,
            'height': end_y - start_y,
            'view_offset': {
                'x': view_offset_x,
                'y': view_offset_y
            }
        }