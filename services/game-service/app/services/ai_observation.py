from __future__ import annotations

from dataclasses import dataclass

import numpy as np


CELL_TERRAIN: dict[int, float] = {
    0: 0.0,
    1: 1.0,
    2: 0.5,
    3: 0.0,
    4: 0.0,
    5: 0.25,
}

DEFAULT_WINDOW_SIZE: int = 15
GRID_CHANNELS: int = 5
STATS_SIZE: int = 9
GRID_SIZE: int = GRID_CHANNELS * DEFAULT_WINDOW_SIZE * DEFAULT_WINDOW_SIZE


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


def build_observation(
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
    max_enemies: int,
    bombs_left: int,
    max_bombs: int,
    bomb_power: int,
    max_bomb_power: int,
    is_invulnerable: bool,
    speed: float,
    max_speed: float,
    time_left: float,
    time_limit: float,
    enemies_positions: list[tuple[float, float]] | None = None,
    weapons_positions: list[tuple[float, float]] | None = None,
    power_ups_positions: list[tuple[float, float]] | None = None,
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

    grid: np.ndarray = np.stack(
        [terrain_window, ch_self, ch_enemies, ch_weapons, ch_powerups],
        axis=0,
    )

    rel_x: float = float(center_x - start_x) / float(max(1, window_size - 1))
    rel_y: float = float(center_y - start_y) / float(max(1, window_size - 1))
    lives_norm: float = float(lives) / float(max(1, max_lives))
    enemy_norm: float = float(enemy_count) / float(max(1, max_enemies))
    bombs_left_norm: float = float(bombs_left) / float(max(1, max_bombs))
    blast_range_norm: float = float(bomb_power) / float(max(1, max_bomb_power))
    invulnerable_val: float = 1.0 if is_invulnerable else 0.0
    speed_norm: float = float(speed) / float(max(1.0, max_speed))
    time_left_norm: float = float(time_left) / float(max(1.0, time_limit)) if time_limit > 0 else 0.0

    stats: list[float] = [
        rel_x,
        rel_y,
        lives_norm,
        enemy_norm,
        bombs_left_norm,
        blast_range_norm,
        invulnerable_val,
        speed_norm,
        time_left_norm,
    ]

    return ObservationData(
        grid_values=grid.flatten().tolist(),
        stats_values=stats,
    )
