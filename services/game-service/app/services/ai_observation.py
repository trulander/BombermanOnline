from __future__ import annotations

import numpy as np


def build_basic_observation(
    *,
    map_grid: list | np.ndarray,
    map_width: int,
    map_height: int,
    cell_size: int,
    entity_x: float,
    entity_y: float,
    lives: int,
    max_lives: int,
    enemy_count: int,
    window_size: int = 15,
) -> list[float]:
    width_cells = max(1, map_width)
    height_cells = max(1, map_height)
    world_width = max(1.0, float(width_cells * cell_size))
    world_height = max(1.0, float(height_cells * cell_size))
    lives_denominator = max(1, max_lives)
    map_area = max(1, width_cells * height_cells)

    x_norm = float(entity_x) / world_width
    y_norm = float(entity_y) / world_height
    lives_norm = float(lives) / float(lives_denominator)
    enemy_norm = float(enemy_count) / float(map_area)
    width_norm = float(width_cells) / 50.0
    height_norm = float(height_cells) / 50.0

    grid_array = np.asarray(map_grid, dtype=np.float32)
    if grid_array.ndim != 2:
        grid_array = np.zeros((height_cells, width_cells), dtype=np.float32)

    center_x = int(entity_x / float(cell_size)) if cell_size > 0 else 0
    center_y = int(entity_y / float(cell_size)) if cell_size > 0 else 0
    half = window_size // 2

    max_start_x = max(0, grid_array.shape[1] - window_size)
    max_start_y = max(0, grid_array.shape[0] - window_size)
    start_x = min(max(center_x - half, 0), max_start_x)
    start_y = min(max(center_y - half, 0), max_start_y)

    window = grid_array[start_y:start_y + window_size, start_x:start_x + window_size]
    if window.shape[0] != window_size or window.shape[1] != window_size:
        padded = np.zeros((window_size, window_size), dtype=np.float32)
        padded[:window.shape[0], :window.shape[1]] = window
        window = padded

    return window.flatten().tolist() + [
        x_norm,
        y_norm,
        lives_norm,
        enemy_norm,
        width_norm,
        height_norm,
    ]

