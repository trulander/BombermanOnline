# API Reference
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/api.md)

This document describes all available RESTful API endpoints and WebSocket events provided by the `WebAPI Service`.

## RESTful API

All API endpoints are available under the prefix `/api/v1`.

### Resource: Games (`/games`)

#### `POST /games`

Creates a new game session.

*   **Description**: Initiates the process of creating a new game. The service sends a command to NATS, and the `Game Allocator Service` allocates a `Game Service` instance for the game. The actual creation happens asynchronously.
*   **Request Body**: `GameCreateSettings` (JSON)

    ```json
    {
      "game_mode": "CAMPAIGN",
      "max_players": 4,
      "player_start_lives": 3,
      "enable_enemies": true,
      "map_chain_id": null,
      "map_template_id": null,
      "respawn_enabled": false,
      "friendly_fire": false,
      "time_limit": 300,
      "score_limit": 10,
      "rounds_count": 15
    }
    ```
*   **Successful Response (200 OK)**:

    ```json
    {
      "success": true,
      "game_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
    }
    ```
*   **Error Response (500 Internal Server Error)**:

    ```json
    {
      "detail": "Error message from the service"
    }
    ```

### Resource: Proxy for Game Service (`/game-service`)

#### `ANY /game-service/{game_id}/{path:path}`

A universal proxy endpoint for interacting with the `Game Service`.

*   **Description**: This endpoint forwards any HTTP request (GET, POST, PUT, DELETE, etc.) to the `Game Service` instance that is handling the specified game. The `WebAPI Service` finds the address of the required instance in the cache (Redis) and fully proxies the request, including the method, headers, parameters, and body.
*   **Path Parameters**:
    *   `game_id` (string, required): The unique identifier for the game.
    *   `path` (string, required): The path that will be passed to the `Game Service`. For example, if you make a request to `/api/v1/game-service/a1b2c3/players/p1`, the request will be forwarded to `/players/p1` in the `Game Service`.
*   **Responses**:
    *   **2xx/4xx/5xx**: The response fully corresponds to what the `Game Service` returned.
    *   **404 Not Found**: Returned if the `game_id` is not found in the cache (the game does not exist or has already ended).
    *   **503 Service Unavailable**: Returned if the `Game Service` is unavailable.

## WebSocket API (Socket.IO)

The WebSocket server is available at the path `/socket.io`. The client must establish a connection and then exchange events.

### Events Sent by the Client (Client -> Server)

#### `join_game`

Joins the client to a game room.

*   **Payload**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "player_id": "p1-xyz..." // optional
    }
    ```
*   **Callback**: Returns the result of the operation.

    ```json
    {
      "success": true,
      "player_id": "p1-xyz...",
      "message": null
    }
    ```

#### `input`

Sends the state of the player's controls to the server.

*   **Payload**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "inputs": {
        "up": true,
        "down": false,
        "left": false,
        "right": false
      }
    }
    ```

#### `place_weapon`

Sends a command to use a weapon (e.g., place a bomb).

*   **Payload**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "weapon_type": "bomb"
    }
    ```
*   **Callback**: Returns the result (e.g., whether the bomb was placed successfully).

    ```json
    {
      "success": true,
      "message": "Bomb has been planted"
    }
    ```

#### `get_game_state`

Requests the full current state of the game.

*   **Payload**:

    ```json
    {
      "game_id": "a1b2c3d4-..."
    }
    ```
*   **Callback**: Returns the full game state.

### Events Received by the Client (Server -> Client)

#### `game_update`

The server sends this event when the game state changes.

*   **Payload**: `GameState` - an object containing information about the positions of players, enemies, bombs, etc.

#### `game_over`

The server sends this event when the game is over.

*   **Payload**: An empty object `{}`.

#### `player_disconnected`

The server sends this event when one of the players disconnects.

*   **Payload**:

    ```json
    {
      "player_id": "p2-abc..."
    }
    ```
