[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/architecture/entities.md)

# Game Entities

This document describes the key game entities, their structure, and behavior in the `Game Service`.

## 1. Players

The base `Player` class (`app/entities/player.py`) defines the common characteristics and behavior of all game characters. Specific player types, such as `Bomberman` and `Tank`, inherit from it and add their unique properties.

### 1.1. `Bomberman` (`app/entities/bomberman.py`)

The classic Bomberman game character.

*   **Purpose**: The main player-controlled unit, specializing in placing bombs.
*   **Key Characteristics**:
    *   `unit_type`: `UnitType.BOMBERMAN`
    *   `scale_size`: `0.8` (relative to cell size)
    *   `primary_weapon`: `WeaponType.BOMB` (primary weapon is a bomb)
    *   `primary_weapon_max_count`: `1` (initial maximum number of bombs that can be placed simultaneously)
    *   `primary_weapon_power`: `1` (initial bomb explosion power)
    *   `secondary_weapon`: `None` (no secondary weapon by default)

### 1.2. `Tank` (`app/entities/tank.py`)

The "Tank" game character (if implemented; its full implementation is missing in the current files, but it is mentioned).

*   **Purpose**: An alternative player-controlled unit, presumably with different characteristics (e.g., higher durability, different weapon).
*   **Key Characteristics**:
    *   `unit_type`: `UnitType.TANK`
    *   `scale_size`: Should be defined (likely larger than Bomberman).
    *   `primary_weapon`: Probably `WeaponType.BULLET` or other.
    *   `secondary_weapon`: May have a unique secondary weapon.

## 2. Map (`app/entities/map.py`)

The `Map` class represents the game grid and manages the state of cells, as well as player and enemy spawn positions.

*   **Purpose**: To store and manage the two-dimensional game board grid, define cell types, and provide helper functions for game logic.
*   **Key Properties**:
    *   `width`: Map width in cells.
    *   `height`: Map height in cells.
    *   `grid`: A two-dimensional NumPy array representing the map grid, where each cell has a type from `CellType`.
    *   `changed_cells`: A list of tracked cell changes to be sent to clients.
*   **Key Methods**:
    *   `load_from_template(grid_data: List[List[int]])`: Loads the map from a data array.
    *   `get_cell_type(x, y) -> CellType`: Returns the cell type at the given coordinates.
    *   `set_cell_type(x, y, cell_type: CellType)`: Sets the cell type and tracks changes.
    *   `is_wall(x, y)`, `is_breakable_block(x, y)`, `is_solid(x, y)`, `is_empty(x, y)`: Helper methods to check the cell type.
    *   `destroy_block(x, y)`: Turns a breakable block into an empty cell.
    *   `get_empty_cells()`: Returns a list of coordinates of empty cells.
    *   `get_player_spawn_positions()`: Returns a list of coordinates for player spawns.
    *   `get_enemy_spawn_positions()`: Returns a list of coordinates for enemy spawns.
    *   `get_changes()`, `clear_changes()`: Manage the list of changed cells.

### 2.1. Cell Types (`app/entities/cell_type.py`)

The `CellType` enumeration defines the possible types of cells on the map:

*   `EMPTY = 0`: An empty cell that can be moved through.
*   `SOLID_WALL = 1`: A solid wall that cannot be destroyed.
*   `BREAKABLE_BLOCK = 2`: A breakable block that can be destroyed by an explosion.
*   `PLAYER_SPAWN = 3`: A player spawn point.
*   `ENEMY_SPAWN = 4`: An enemy spawn point.

## 3. Game Modes (`app/entities/game_mode.py`)

The `GameModeType` enumeration defines the available game modes:

*   `CAMPAIGN = "CAMPAIGN"`: A progression-oriented mode, focused on PVE (players vs. environment) with co-op possibility.
*   `FREE_FOR_ALL = "FREE_FOR_ALL"`: A "every man for himself" mode where each player competes individually.
*   `CAPTURE_THE_FLAG = "CAPTURE_THE_FLAG"`: A team-based mode where the goal is to capture the enemy's flag.

(Detailed logic for each mode is implemented in `app/services/modes/`.)

## 4. Weapons (`app/entities/weapon.py`)

*   **`WeaponType`**: Enumeration of weapon types (`BOMB`, `BULLET`, `MINE`).
*   **`WeaponAction`**: Enumeration of possible weapon actions (`PLACEWEAPON1`, `PLACEWEAPON2`, `ACTIVATEWEAPON1`, `ACTIVATEWEAPON2`).
*   **`Weapon`**: The base class for all weapons, defining common properties and behavior (explosions, collisions).

## 5. Enemies (`app/entities/enemy.py`)

*   **`EnemyType`**: Enumeration of enemy types (e.g., `BALLOOM`, `ONEAL`, `DAQAN`).
*   **`Enemy`**: The base class for all enemies with common properties and behavior (movement, interaction with the player).

## 6. Power-Ups (`app/entities/power_up.py`)

*   **`PowerUpType`**: Enumeration of power-up types (e.g., `BOMB_UP`, `FIRE_UP`, `SPEED_UP`, `PIERCE_BOMB`, `IMMUNITY`).
*   **`PowerUp`**: The base class for all power-ups, defining their effects on players.
