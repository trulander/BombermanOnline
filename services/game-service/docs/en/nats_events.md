[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/nats_events.md)

# Game Service NATS Events

Game Service actively uses NATS for asynchronous message exchange. This includes receiving commands from players/other services and sending game state updates.

## 1. Incoming Events (Service Subscriptions)

The service subscribes to the following events. Commands are usually sent with a `reply` field to receive a response.

### `game.create` - deprecated!

-   **Description**: Initiates the creation of a new game session.
-   **Direction**: Client/WebAPI -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "unique_game_id_optional",
      "new_game_settings": { // Optional, see GameCreateSettings
        "game_mode": "campaign", // "campaign", "free_for_all", "capture_the_flag"
        "max_players": 4,
        "team_count": 1,
        "player_start_lives": 3,
        "enable_enemies": true,
        "map_chain_id": "map_chain_id_optional",
        "map_template_id": "map_template_id_optional",
        "respawn_enabled": false,
        "friendly_fire": false,
        "time_limit": 300, // seconds
        "score_limit": 10,
        "rounds_count": 15
      }
    }
    ```
    If `new_game_settings` is not provided, `game_id` is mandatory, and the game will be created with default settings or based on individual `game_mode`, `map_template_id`, `map_chain_id` fields from the payload.
-   **Handler in Game Service**: `GameCoordinator.game_create()`.
-   **Response (to `msg.reply`)**: JSON object.
    -   Success: `{"success": true, "game_id": "created_game_id"}`
    -   Error: `{"success": false, "message": "error_text"}`

### `game.join`

-   **Description**: Request to join an existing game.
-   **Direction**: Client -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "game_id",
      "player_id": "player_id",
      "unit_type": "bomberman" // Optional, "bomberman" or "tank"
    }
    ```
-   **Handler**: `GameCoordinator.game_join()`.
-   **Response (to `msg.reply`)**: JSON object.
    -   Success: `{"success": true, "player_id": "player_id", "game_state": { /* initial game state */ }}`
    -   Error: `{"success": false, "message": "error_text"}` (e.g., "Game not found", "Game is full")

### `game.input`

-   **Description**: Transmitting input commands from the player.
-   **Direction**: Client -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "game_id",
      "player_id": "player_id",
      "inputs": {
        "up": false,
        "down": false,
        "left": true,
        "right": false,
        "weapon1": false, // Primary weapon (bomb/bullet)
        "action1": false, // additional action for primary weapon
        "weapon2": false  // Secondary weapon (mine)
      }
    }
    ```
-   **Handler**: `GameCoordinator.game_input()`.
-   **Response**: Usually none (fire-and-forget), but if `msg.reply` is specified, the service will send `null` or an empty response on success, or an error.


### `game.place_weapon`

-   **Description**: Universal command for a player to use a weapon.
-   **Direction**: Client -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "game_id",
      "player_id": "player_id",
      "weapon_type": "bomb" // "bomb", "bullet", "mine". Optional, defaults to player's primary weapon.
    }
    ```
-   **Handler**: `GameCoordinator.game_place_weapon()`.
-   **Response (to `msg.reply`)**: `{"success": true/false, "message": "optional_message"}`.

### `game.get_state`

-   **Description**: Request to get the current full game state.
-   **Direction**: Client -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "game_id"
    }
    ```
-   **Handler**: `GameCoordinator.game_get_state()`.
-   **Response (to `msg.reply`)**: JSON object.
    -   Success: `{"success": true, "game_state": { /* current game state */ }, "full_map": { /* full map */ }}`
    -   Error: `{"success": false, "message": "error_text"}`

### `game.disconnect`

-   **Description**: Notification of a player disconnecting from the game.
-   **Direction**: Client/WebAPI -> Game Service.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "game_id": "game_id",
      "player_id": "player_id"
    }
    ```
-   **Handler**: `GameCoordinator.game_player_disconnect()`.
-   **Response (to `msg.reply`)**: `{"success": true/false, "message": "optional_message"}`.

## 2. Outgoing Events (Service Publications)

The service publishes the following events to notify clients and other systems.

### `game.update.{game_id}`

-   **Description**: Regular game state update.
-   **Direction**: Game Service -> Clients.
-   **Data (Payload)**: JSON object representing the current game state (see `GameModeService.get_state()` for structure).
    Example key fields:
    ```json
    {
      "players": { /* ... */ },
      "teams": { /* ... */ },
      "enemies": [ /* ... */ ],
      "weapons": [ /* ... */ ],
      "powerUps": [ /* ... */ ],
      "map": {
        "changedCells": [{"x": 1, "y": 2, "type": 0}],
      },
      "score": 0,
      "level": 1,
      "gameOver": false,
      "status": "active",
      "gameMode": "campaign"
    }
    ```
-   **Source**: Published from `GameCoordinator.start_game_loop()`.

### `game.over.{game_id}`

-   **Description**: Notification of game session end.
-   **Direction**: Game Service -> Clients.
-   **Data (Payload)**: Empty JSON object `{}`.
-   **Source**: Published from `GameCoordinator.start_game_loop()` when the game becomes inactive.

### `game.player_disconnected.{game_id}`

-   **Description**: Notification to other players that one player has disconnected.
-   **Direction**: Game Service -> Clients.
-   **Data (Payload)**: JSON object.
    ```json
    {
      "player_id": "disconnected_player_id"
    }
    ```
-   **Source**: Published from `EventService.handle_player_disconnect()` after successful disconnection processing.
