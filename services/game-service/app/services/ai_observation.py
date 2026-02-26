from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np


CELL_TERRAIN: dict[int, float] = {
    0: 0.0,
    1: 1.0,
    2: 0.5,
    3: 0.0,
    4: 0.0,
    5: 0.25,
}

DEFAULT_WINDOW_SIZE: int = 7
GRID_PLAYER_INFERENCE_CHANNELS: int = 6
GRID_ENEMY_INFERENCE_CHANNELS: int = 4
# closest_enemy, lives, enemies, bombs_left, invuln, in_blast_zone, time_left
STATS_SIZE: int = 7
GRID_ENEMY_INFERENCE_SIZE: int = GRID_ENEMY_INFERENCE_CHANNELS * DEFAULT_WINDOW_SIZE * DEFAULT_WINDOW_SIZE
GRID_PLAYER_INFERENCE_SIZE: int = GRID_PLAYER_INFERENCE_CHANNELS * DEFAULT_WINDOW_SIZE * DEFAULT_WINDOW_SIZE


@dataclass
class ObservationData:
    grid_values: list[float]
    stats_values: list[float]


def _world_to_cell(coord: float, cell_size: int) -> int:
    if cell_size > 0:
        return int(coord / float(cell_size))
    return 0


def _calc_window_origin(
    *,
    center: int,
    half: int,
    grid_extent: int,
    window_size: int,
) -> int:
    max_start: int = max(0, grid_extent - window_size)
    return min(max(center - half, 0), max_start)


def _place_on_channel(
    *,
    channel: np.ndarray,
    positions: list[tuple[float, float]],
    cell_size: int,
    start_x: int,
    start_y: int,
    window_size: int,
) -> None:
    for wx, wy in positions:
        gx: int = _world_to_cell(coord=wx, cell_size=cell_size)
        gy: int = _world_to_cell(coord=wy, cell_size=cell_size)
        lx: int = gx - start_x
        ly: int = gy - start_y
        if 0 <= lx < window_size and 0 <= ly < window_size:
            channel[ly, lx] = 1.0

def get_closest_enemy_distance(
        *,
        px: float,
        py: float,
        enemies: list[Tuple[float, float]],
        cell_size: int,
        map_width: int,
        map_height: int
) -> float:
    """
    Calculate normalized distance to the closest enemy in grid cells.

    Returns a value from 0.0 (enemy in the same cell) to 1.0 (maximum distance on map).
    If no enemies exist, returns 1.0.

    Uses grid-based distance calculation for better performance and simpler logic.
    Positions are rounded to nearest cell coordinates.

    Args:
        px: Entity X coordinate in pixels
        py: Entity Y coordinate in pixels

    Returns:
        Normalized distance (0.0 to 1.0)
    """

    # Convert player position to grid cells (rounded to nearest cell)
    player_cell_x: int = round(px / cell_size)
    player_cell_y: int = round(py / cell_size)

    # Calculate maximum possible distance on the map in cells (diagonal from corner to corner)
    max_distance_cells: float = math.hypot(map_width, map_height)

    # If no enemies exist, return maximum distance (normalized to 1.0)
    if not enemies:
        return 1.0

    # Find closest enemy distance in cells
    min_dist_cells: float = max_distance_cells
    for e in enemies:
        # Convert enemy position to grid cells (rounded to nearest cell)
        enemy_cell_x: int = round(e[0] / cell_size)
        enemy_cell_y: int = round(e[1] / cell_size)

        # Calculate distance in cells using Manhattan or Euclidean distance
        # Using Euclidean for more accurate distance representation
        dist_cells: float = math.hypot(
            enemy_cell_x - player_cell_x,
            enemy_cell_y - player_cell_y
        )
        if dist_cells < min_dist_cells:
            min_dist_cells = dist_cells

    # If enemy is in the same cell (distance = 0), return 0.0
    if min_dist_cells <= 0.0:
        return 0.0

    # Normalize distance: 0.0 (same cell) to 1.0 (maximum distance)
    normalized: float = min(1.0, min_dist_cells / max_distance_cells)
    return normalized


def build_observation(
    *,
    is_player: bool,
    is_cooperative: bool,
    map_grid: list | np.ndarray,
    map_width: int,
    map_height: int,
    cell_size: int,
    entity_x: float,
    entity_y: float,
    lives: int,
    max_lives: int,
    enemy_count: int,
    max_enemies: int,
    bombs_left: int,
    max_bombs: int,
    is_invulnerable: bool,
    in_blast_zone: float,
    time_left: float,
    time_limit: float,
    closest_enemy: float,
    enemies_positions: list[tuple[float, float]],
    players_positions: list[tuple[float, float]],
    weapons_positions: list[tuple[float, float]],
    power_ups_positions: list[tuple[float, float]],
    window_size: int = DEFAULT_WINDOW_SIZE,
) -> ObservationData:
    width_cells: int = max(1, map_width)
    height_cells: int = max(1, map_height)

    grid_array: np.ndarray = np.asarray(map_grid, dtype=np.float32)
    if grid_array.ndim != 2:
        grid_array = np.zeros((height_cells, width_cells), dtype=np.float32)

    terrain: np.ndarray = np.zeros_like(grid_array)
    for cell_val, norm_val in CELL_TERRAIN.items():
        terrain[grid_array == cell_val] = norm_val

    center_x: int = _world_to_cell(coord=entity_x, cell_size=cell_size)
    center_y: int = _world_to_cell(coord=entity_y, cell_size=cell_size)
    half: int = window_size // 2

    start_x: int = _calc_window_origin(
        center=center_x,
        half=half,
        grid_extent=terrain.shape[1],
        window_size=window_size,
    )

    start_y: int = _calc_window_origin(
        center=center_y,
        half=half,
        grid_extent=terrain.shape[0],
        window_size=window_size,
    )

    terrain_window: np.ndarray = terrain[
        start_y:start_y + window_size,
        start_x:start_x + window_size,
    ].copy()
    if terrain_window.shape[0] != window_size or terrain_window.shape[1] != window_size:
        padded: np.ndarray = np.ones((window_size, window_size), dtype=np.float32)
        padded[:terrain_window.shape[0], :terrain_window.shape[1]] = terrain_window
        terrain_window = padded

    ch_self: np.ndarray = np.zeros((window_size, window_size), dtype=np.float32)
    player_lx: int = center_x - start_x
    player_ly: int = center_y - start_y
    if 0 <= player_lx < window_size and 0 <= player_ly < window_size:
        ch_self[player_ly, player_lx] = 1.0

    ch_enemies: np.ndarray = np.zeros((window_size, window_size), dtype=np.float32)
    if enemies_positions:
        _place_on_channel(
            channel=ch_enemies,
            positions=enemies_positions,
            cell_size=cell_size,
            start_x=start_x,
            start_y=start_y,
            window_size=window_size,
        )

    ch_players: np.ndarray = np.zeros((window_size, window_size), dtype=np.float32)
    if players_positions:
        _place_on_channel(
            channel=ch_players,
            positions=players_positions,
            cell_size=cell_size,
            start_x=start_x,
            start_y=start_y,
            window_size=window_size,
        )

    ch_weapons: np.ndarray = np.zeros((window_size, window_size), dtype=np.float32)
    if weapons_positions:
        _place_on_channel(
            channel=ch_weapons,
            positions=weapons_positions,
            cell_size=cell_size,
            start_x=start_x,
            start_y=start_y,
            window_size=window_size,
        )

    ch_powerups: np.ndarray = np.zeros((window_size, window_size), dtype=np.float32)
    if power_ups_positions:
        _place_on_channel(
            channel=ch_powerups,
            positions=power_ups_positions,
            cell_size=cell_size,
            start_x=start_x,
            start_y=start_y,
            window_size=window_size,
        )
    if is_player:
        grid: np.ndarray = np.stack(
            [terrain_window, ch_self, ch_players, ch_weapons, ch_enemies, ch_powerups],
            axis=0,
        )
    else:
        grid: np.ndarray = np.stack(
            [terrain_window, ch_self, ch_players, ch_weapons],
            axis=0,
        )

    lives_norm: float = float(lives) / float(max(1, max_lives))
    enemy_norm: float = float(enemy_count) / float(max(1, max_enemies))
    bombs_left_norm: float = float(bombs_left) / float(max(1, max_bombs))
    invulnerable_val: float = 1.0 if is_invulnerable else 0.0
    time_left_norm: float = float(time_left) / float(max(1.0, time_limit)) if time_limit > 0 else 0.0

    stats: list[float] = [
        closest_enemy,
        lives_norm,
        enemy_norm,
        bombs_left_norm,
        invulnerable_val,
        in_blast_zone,
        time_left_norm,
    ]

    return ObservationData(
        grid_values=grid.flatten().tolist(),
        stats_values=stats,
    )
