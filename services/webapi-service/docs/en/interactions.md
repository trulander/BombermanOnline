# Interaction with Other Services
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/interactions.md)

The `WebAPI Service` is a central hub that coordinates data flows between clients and backend services. The interaction is built on a combination of synchronous (HTTP) and asynchronous (NATS) protocols.

## Sequence Diagram: Creating a Game

This scenario shows how a new game session is created. The process is initiated by the client and requires the participation of the `Game Allocator Service` to allocate resources.

```mermaid
sequenceDiagram
    participant C as Client
    participant W as WebAPI Service
    participant N as NATS
    participant GA as Game Allocator
    participant GS as Game Service

    C->>+W: POST /api/v1/games (game parameters)
    W->>+N: Request game.assign.request (game_id, requirements)
    Note right of W: Requests allocation of<br>a Game Service instance
    N->>+GA: Receives request
    GA->>GA: Selects a suitable<br>Game Service instance
    GA-->>-N: Response (instance_id)
    N-->>-W: Receives instance_id (Game Service address)
    W->>W: Caches the game_id -> instance_id link in Redis
    W->>+N: Publishes command game.create.{instance_id} (parameters)
    N->>+GS: Delivers the command to the specific instance
    GS->>GS: Creates the game room
    GS-->>-N: Response (success, game_id)
    N-->>-W: Receives response
    W-->>-C: 200 OK (game_id)
```

**Process Description:**
1.  The **Client** sends an HTTP POST request to `/api/v1/games`, passing the settings for the future game.
2.  The **WebAPI Service** receives the request and generates a unique `game_id`.
3.  The WebAPI sends a `game.assign.request` to NATS to find a suitable `Game Service` for the new game.
4.  The **Game Allocator Service**, subscribed to this topic, receives the request, selects the least loaded `Game Service` instance, and returns its address (`instance_id`).
5.  The WebAPI caches the received address in **Redis**, linking it to the `game_id`.
6.  The WebAPI publishes a `game.create` command to NATS, directing it to the specific `Game Service` instance (using the `instance_id` in the message topic).
7.  The **Game Service** receives the command, creates the game, and returns a confirmation.
8.  The WebAPI sends a successful response to the client.

## Sequence Diagram: Gameplay (WebSocket)

This scenario describes the main gameplay loop: joining a game, exchanging data in real-time, and receiving updates.

```mermaid
sequenceDiagram
    participant C as Client
    participant W as WebAPI Service
    participant N as NATS
    participant GS as Game Service

    C->>+W: WebSocket: 'join_game' event (game_id)
    W->>W: Finds Game Service address in cache (Redis)
    W->>+N: Publishes command game.join.{instance_id}
    N->>+GS: Delivers command
    GS->>GS: Adds player to the room
    GS-->>-N: Response (success)
    N-->>-W: Receives response
    W->>W: Subscribes to NATS topic 'game.update.{game_id}'
    W-->>-C: WebSocket: response to 'join_game' (success)

    loop Game Loop
        C->>W: WebSocket: 'input' event (input data)
        W->>N: Publishes command game.input.{instance_id}
    end

    Note over GS: Game Service processes input, updates state

    GS->>N: Publishes event 'game.update.{game_id}' (new state)
    N->>W: Delivers update
    W->>C: WebSocket: 'game_update' event (new state)
```

**Process Description:**
1.  After the game is created, the **Client** sends a `join_game` WebSocket event.
2.  The **WebAPI Service** finds the `Game Service` address associated with the `game_id` in the Redis cache.
3.  The WebAPI sends a `game.join` command to NATS for the corresponding `Game Service`.
4.  The **Game Service** adds the player and confirms the join.
5.  Upon receiving confirmation, the WebAPI subscribes to the `game.update.{game_id}` topic in NATS to receive all updates for this game.
6.  The client sends action data (e.g., movement) via an `input` WebSocket event.
7.  The WebAPI broadcasts this event to NATS as a `game.input` command for the `Game Service`.
8.  The **Game Service** processes the player's actions, updates the game state, and publishes it to the `game.update.{game_id}` topic.
9.  The WebAPI, being subscribed to this topic, receives the update and immediately forwards it to all clients in the corresponding game room via WebSocket.

## Sequence Diagram: Getting List of Games

This scenario shows how the WebAPI aggregates games from all `Game Service` instances to provide a unified list.

```mermaid
sequenceDiagram
    participant Frontend
    participant WebAPI as WebAPI Service
    participant NATS
    participant Allocator as Game Allocator Service
    participant Consul
    participant GS1 as Game Service 1
    participant GS2 as Game Service 2
    participant GSN as Game Service N

    Frontend->>+WebAPI: GET /api/v1/games
    WebAPI->>+NATS: Request game.instances.request
    NATS->>+Allocator: Receives request
    Allocator->>Consul: Get healthy instances
    Consul-->>Allocator: [instance1, instance2, ...]
    Allocator-->>-NATS: Response {"instances": [...]}
    NATS-->>-WebAPI: Receives list of instances
    
    par Parallel HTTP Requests
        WebAPI->>GS1: GET /games/api/v1/games/
        GS1-->>WebAPI: [game1, game2, ...]
    and
        WebAPI->>GS2: GET /games/api/v1/games/
        GS2-->>WebAPI: [game3, game4, ...]
    and
        WebAPI->>GSN: GET /games/api/v1/games/
        GSN-->>WebAPI: [gameN, ...]
    end
    
    WebAPI->>WebAPI: Merge and apply filters
    WebAPI-->>-Frontend: Unified list of games
```

**Process Description:**
1.  The **Frontend** sends an HTTP GET request to `/api/v1/games` with optional filter parameters.
2.  The **WebAPI Service** requests a list of all healthy `Game Service` instances from `Game Allocator Service` via NATS using the `game.instances.request` event.
3.  The **Game Allocator Service** queries **Consul** to get the list of healthy `game-service` instances.
4.  The Allocator returns the list of instances (addresses and ports) to WebAPI via NATS.
5.  The WebAPI makes parallel HTTP requests to each `Game Service` instance, requesting their list of games with the same filter parameters.
6.  Each **Game Service** instance returns its own list of games.
7.  The WebAPI merges all results, applies pagination (limit/offset), and returns the unified list to the client.

## Sequence Diagram: HTTP Request Proxying

This scenario shows how the WebAPI forwards standard HTTP requests (e.g., to get detailed game statistics) directly to the `Game Service`.

```mermaid
sequenceDiagram
    participant C as Client
    participant W as WebAPI Service
    participant Cache as Redis Cache
    participant GS as Game Service

    C->>+W: GET /api/v1/game-service/{game_id}/stats
    W->>+Cache: Request: get(games:{game_id})
    Cache-->>-W: Response: instance_id (Game Service address)
    alt Address found
        W->>+GS: HTTP GET /stats (proxies request)
        GS-->>-W: HTTP 200 OK (statistics data)
        W-->>-C: HTTP 200 OK (proxies response)
    else Address not found
        W-->>-C: HTTP 404 Not Found
    end
```

**Process Description:**
1.  The **Client** sends an HTTP request to an endpoint intended for proxying, e.g., `.../game-service/{game_id}/stats`.
2.  The **WebAPI Service** extracts the `game_id` from the URL.
3.  It queries its **cache (Redis)** to find the `instance_id` (address) of the `Game Service` that is handling this game.
4.  If the address is found, the WebAPI, using an HTTP client (`httpx`), creates an identical request and sends it to `http://{instance_id}/stats`.
5.  The **Game Service** processes the request and returns a response.
6.  The WebAPI fully proxies the response (body, headers, status code) back to the client.
7.  If the address is not found in the cache, the WebAPI returns a `404 Not Found` error.
