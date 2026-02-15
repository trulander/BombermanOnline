[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/player_commands_and_actions.md)

# Player Commands and Their Processing

This section describes in detail how the `game-service` receives, interprets, and processes commands coming from players. These commands control character movement, weapon use, and other key game actions.

## 1. Sources of Player Commands

The main way for a player to convey their intentions in the game is through NATS messages. Two key events handle most of the actions:

-   **`game.input`**: Transmits the state of movement buttons and primary/secondary actions (usually weapon use).
-   **`game.place_weapon`**: An explicit command to use a specific type of weapon.

These events are described in detail in the [NATS Events](nats_events.md) section.

## 2. Processing Movement and Basic Action Commands (`game.input`)

The `game.input` event carries information about the current state of the player's pressed keys.

-   **Payload**: Contains `game_id`, `player_id`, and an `inputs` dictionary (of type `Inputs` from `app/entities/player.py`):
    ```json
    {
      "up": false, "down": false, "left": true, "right": false, // Movement
      "weapon1": false, // Primary weapon/action
      "action1": false, // Primary weapon additional action
      "weapon2": false  // Secondary weapon/action
    }
    ```
-   **Initial Processing**:
    1.  `EventService` receives the message and passes it to `GameCoordinator`.
    2.  `GameCoordinator` finds the corresponding `GameService` instance and the `Player` object within it.
    3.  The `player.set_inputs(inputs)` method is called.
        -   Inside `Player.set_inputs()`:
            -   The internal `player.inputs` dictionary is updated.
            -   If `player.unit_type` is `UnitType.TANK`, `player.direction` is also updated based on the pressed movement keys (up, down, left, right). This direction is used to determine where the tank will shoot. For `UnitType.BOMBERMAN`, the direction is usually determined by the last movement vector, which is calculated in `GameModeService`.

-   **Logic in the Game Loop (`GameModeService`)**:
    The saved state of `player.inputs` is used in the `update_player()` method (or similar) within the active `GameModeService` (e.g., `CampaignMode`, `FreeForAllMode`) during each tick of the game loop:
    -   **Movement**: Based on the `up`, `down`, `left`, `right` flags and `player.speed`, the new player position is calculated. Collision detection with map boundaries, walls (`CellType.SOLID_WALL`), breakable blocks (`CellType.BREAKABLE_BLOCK`), and other entities is applied.
    -   **Weapon Use (from `weapon1`, `weapon2`)**:
        -   If the `weapon1` or `weapon2` flag in `player.inputs` is set to `True`, `GameModeService` initiates the logic for using the corresponding weapon (`player.primary_weapon` or `player.secondary_weapon`).
        -   This usually involves calling the `game_mode_service.place_weapon(player_id, weapon_type)` method, which checks if the player can use this weapon (e.g., `player.max_weapons` for bombs is not exceeded, there is no cooldown).
        -   Upon successful validation, a weapon object (e.g., `Bomb`, `Mine`) is created and placed on the map, or in the case of a `Bullet`, it is created and starts moving.

## 3. Processing Explicit Weapon Use Command (`game.place_weapon`)

This event allows the player to explicitly specify which type of weapon they want to use.

-   **Payload**: Contains `game_id`, `player_id`, and an optional `weapon_type` (from `WeaponType`).
    ```json
    {
      "game_id": "game_id",
      "player_id": "player_id",
      "weapon_type": "bomb" // "bomb", "bullet", "mine"
    }
    ```
-   **Processing**:
    1.  `EventService` -> `GameCoordinator`.
    2.  `GameCoordinator` calls `game_service.place_weapon(player_id, weapon_type)`.
    3.  `GameService` delegates the call to `game_mode_service.place_weapon(player_id, weapon_type)`.
    4.  In `GameModeService.place_weapon()`:
        -   The type of weapon to be used is determined. If `weapon_type` is not specified in the payload, `player.primary_weapon` may be used by default.
        -   **Checks**:
            -   Whether the player has enough "charges" or if the limit is not exceeded (e.g., `active_bombs_count < player.max_weapons` for bombs).
            -   Whether there is an active cooldown for using this type of weapon.
        -   **Creation and Activation**:
            -   If the checks pass, a weapon instance (`Bomb`, `Bullet`, `Mine`) is created.
            -   For `Bomb` and `Mine`: the object is placed on the map in the player's current or adjacent cell. Its timer (`weapon.timer`) starts counting down in its `update()` method, but the actual bomb explosion (calling `bomb.activate()`) is initiated by `GameModeService` after `GameSettings.bomb_timer` expires. For a mine, `mine.trigger()` is called on contact, and then its own `update()` can lead to `activate()`.
            -   For `Bullet`: the object is created with the direction `player.direction` and speed `player.speed` (or `GameSettings.bullet_speed`). The bullet starts moving immediately.

## 4. Impact of Player Unit Type and Game Modes

### 4.1. Unit Type (`Player.unit_type`)

The unit type chosen by the player (`BOMBERMAN` or `TANK`) significantly affects the available commands and their interpretation:

-   **`UnitType.BOMBERMAN`**:
    -   `primary_weapon`: `WeaponType.BOMB`.
    -   `player.primary_weapon_max_count`: Determines how many bombs the player can place simultaneously. Increased by the `PowerUpType.BOMB_UP` power-up.
    -   `player.primary_weapon_power`: Determines the explosion radius of bombs. Increased by the `PowerUpType.BOMB_POWER_UP` power-up.
    -   Standard 4-directional movement.

-   **`UnitType.TANK`**:
    -   `primary_weapon`: `WeaponType.BULLET`.
    -   `secondary_weapon`: `WeaponType.MINE`.
    -   `player.primary_weapon_max_count`: Usually higher (e.g., 2), allowing for firing multiple bullets in a row (cooldown logic between shots is handled in `GameModeService`).
    -   `player.primary_weapon_power`: Can affect bullet damage (if such a mechanic is added) or other characteristics.
    -   `player.secondary_weapon_max_count`:
    -   `player.secondary_weapon_power`:
    -   `player.direction`: Updated based on movement commands and used to determine the bullet's firing direction. The tank shoots in the direction it is "facing".

### 4.2. Game Modes (`GameModeService` and its implementations)

Although the basic logic for processing movement and weapon use commands is mostly the same and implemented in `GameModeService`, specific mode rules can affect the outcome:

-   **`CampaignMode`**:
    -   Commands work as standard. Level objectives (destroying enemies, reaching the exit) do not affect the commands themselves, but the win/loss conditions.
-   **`FreeForAllMode`**:
    -   Commands work as standard. `friendly_fire` from `GameSettings` determines if one's own bombs will cause damage.
-   **`CaptureTheFlagMode`**:
    -   Movement and weapon use are standard.
    -   Interaction with flags (picking up, placing on the base) is usually implemented through collision logic during movement, rather than separate "commands". That is, the command "move to the cell with the flag" results in picking it up, if possible according to the mode's rules.

## 5. "Default" Commands and Implicit Actions

-   **No Input**: If the player does not press any movement buttons, their character stands still.
-   **Facing/Attack Direction**:
    -   For `BOMBERMAN`: Bombs and mines are placed on the current or adjacent cell. The direction is not as critical for the act of placing itself.
    -   For `TANK`: The firing direction is determined by `player.direction`, which changes with movement. If the tank is stationary and presses "fire", it shoots in the last remembered direction.
-   **Automatic Actions**: Some actions can occur automatically in response to other events, rather than direct commands:
    -   Bomb explosion on a timer.
    -   Mine activation on contact.
    -   Picking up power-ups by walking over them.

## 6. Role of `GameSettings`

Many parameters from `GameSettings` (global and session-specific) affect command execution:
-   `player_default_speed`, `bullet_speed`: affect movement.
-   `bomb_timer`, `default_bomb_power`, `default_count_bombs`: affect the characteristics and use of bombs.
-   `friendly_fire`: determines if a player can harm themselves or allies with their weapon.

## Conclusion

The command system in `game-service` is built on NATS events that update the player's state. Then, in the main game loop, `GameModeService` uses this state to perform actions such as movement and weapon use, taking into account the player's unit type, the rules of the current game mode, and global game settings. The complexity and nuances of behavior arise from the interaction of these components.
