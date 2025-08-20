# Use Cases
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/use-cases.md)

This section details the main scenarios of user interaction with the system through the `WebAPI Service`.

## Scenario 1: Creating and Starting a New Game

**Goal:** A user wants to create a new game room and start a game.

**Actors:** Client (user), WebAPI Service, Game Allocator Service, Game Service.

**Steps:**

1.  The **user** clicks the "Create Game" button in the client interface.
2.  The **client** sends a `POST` request to the `/api/v1/games` endpoint.
    *   The **request body** contains game parameters: mode (`game_mode`), maximum number of players (`max_players`), etc.
    ```json
    {
      "game_mode": "FREE_FOR_ALL",
      "max_players": 4
    }
    ```
3.  The **WebAPI Service** (`game_routes.py`) receives the request.
4.  `GameService.create_game()` is called, which initiates the process of allocating a game server via NATS (see the diagram in the [Interaction](./interactions.md) section).
5.  After the `Game Allocator` has allocated a `Game Service` instance and it has confirmed the room's creation, the WebAPI returns a successful response to the client.
    *   The **response body** contains the `game_id`.
    ```json
    {
      "success": true,
      "game_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
    }
    ```
6.  The **client** receives the `game_id` and automatically initiates a WebSocket connection to the server.
7.  After establishing the connection, the client sends a `join_game` event.
    ```javascript
    // Example on the client
    const socket = io("http://localhost:5001");
    socket.emit("join_game", { game_id: "a1b2c3d4-..." }, (response) => {
      if (response.success) {
        console.log("Successfully joined the game! Player ID:", response.player_id);
        // Start the gameplay
      }
    });
    ```
8.  The **WebAPI Service** (`socketio_service.py`) processes the `join_game` event, links the client's `sid` with the `game_id`, subscribes to updates from the `Game Service` via NATS, and adds the client to the Socket.IO room for that game.
9.  The game is ready to start. The client can send input commands and will receive state updates.

## Scenario 2: Gameplay

**Goal:** A user in a game controls their character and sees the actions of other players.

**Actors:** Client, WebAPI Service, Game Service, NATS.

**Prerequisite:** The user has successfully joined the game (Scenario 1).

**Steps:**

1.  The **user** presses a movement key (e.g., "up").
2.  The **client** captures this action and sends an `input` event via WebSocket.
    ```javascript
    socket.emit("input", {
      game_id: "a1b2c3d4-...",
      inputs: { up: true, down: false, left: false, right: false }
    });
    ```
3.  The **WebAPI Service** (`socketio_service.py`) receives the event and calls `GameService.send_input()`.
4.  `GameService` via `NatsService` publishes a `game.input` command to NATS, addressing it to the specific `Game Service` instance that is handling the game.
5.  The **Game Service** receives the command and updates the character's position in its internal state.
6.  After updating its state, the **Game Service** publishes the full or partial game state to the `game.update.{game_id}` topic in NATS.
7.  The **WebAPI Service** (`nats_service.py`), being subscribed to this topic, receives the update.
8.  `NatsService` calls the corresponding handler in `SocketIOService` (`handle_game_update`).
9.  **SocketIOService** sends a `game_update` event to all clients in the room for that game.
    ```javascript
    // Client listens for the event
    socket.on("game_update", (gameState) => {
      // Update the canvas, redraw all players and objects
      console.log("New game state:", gameState);
      renderGame(gameState);
    });
    ```
10. The **client** receives the new state and redraws the game world, displaying the character's movement.

This cycle repeats for each action of each player, ensuring real-time game synchronization.

## Scenario 3: Viewing Statistics of a Completed Game

**Goal:** A user wants to view detailed statistics after a match has ended.

**Actors:** Client, WebAPI Service, Game Service.

**Prerequisite:** The game is over.

**Steps:**

1.  The **client** navigates to the match results screen.
2.  To get detailed data (e.g., who defeated whom, accuracy, etc.), the client sends a `GET` request to the proxy endpoint.
    *   **Request URL**: `/api/v1/game-service/{game_id}/statistics`
3.  The **WebAPI Service** (`proxy_routes.py`) handles the request.
4.  It extracts the `game_id` and looks up the address (`instance_id`) of the `Game Service` that handled the game in the **Redis cache**.
5.  After finding the address, the WebAPI forms a new `GET` request to `http://{instance_id}/statistics` and sends it to the **Game Service**.
6.  The **Game Service** queries its database or internal state, generates a statistics report, and returns it as JSON.
7.  The **WebAPI Service** receives the response from the `Game Service` and fully forwards it (including the body, headers, and status code) back to the **client**.
8.  The **client** receives the data and displays it to the user.
