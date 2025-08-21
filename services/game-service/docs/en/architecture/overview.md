[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/architecture/overview.md)

# Game Service Architecture Overview

Game Service is built using a multi-layered architecture aimed at separating responsibilities and ensuring modularity. The main components interact through clearly defined interfaces and events.

## Key Layers and Components:

1.  **Entry Point and Routing (`app/main.py`, `app/routes/`)**:
    -   **FastAPI application (`app/main.py`)**: Initializes the application, middleware (CORS, Prometheus, Auth), connects routers, and manages the lifecycle (startup/shutdown events for initializing/releasing resources, such as DB and NATS connections).
    -   **Routers (`app/routes/map_routes.py`)**: Define HTTP endpoints for interacting with the service (e.g., CRUD operations for map management). Handle HTTP requests, validate data, and call appropriate services.

2.  **Coordinators (`app/coordinators/`)**:
    -   **`GameCoordinator`**: The central component managing the lifecycle of games. It:
        -   Subscribes to NATS events (game creation, player connection, input, etc.) via `EventService`.
        -   Manages a dictionary of active games (`games: dict[str, GameService]`).
        -   Starts and maintains the main game loop (`start_game_loop`), which periodically updates the state of all active games and sends updates via NATS.
        -   Handles creation, joining, input, weapon application, state requests, and player disconnections, delegating these operations to the corresponding `GameService` instance.

3.  **Service Layer (`app/services/`)**:
    -   **`EventService`**: An abstraction for working with NATS. Registers handlers for incoming NATS messages and provides methods for publishing outgoing events. Decodes incoming messages and encodes outgoing ones.
    -   **`GameService`**: Manages the logic of a single game session. Contains an instance of a specific game mode (`GameModeService`). Responsible for adding/removing players, starting/pausing/resuming the game, updating the state by calling `game_mode.update()`, and applying weapons.
    -   **`GameModeService` (and its implementations in `app/services/modes/`)**: An abstract base class for various game modes (`CampaignMode`, `FreeForAllMode`, `CaptureTheFlagMode`). Each mode implements specific logic:
        -   Map initialization (`initialize_map`).
        -   Adding/removing players considering mode rules.
        -   Updating the state of game objects (players, enemies, weapons).
        -   Checking game over conditions (`is_game_over`).
        -   Handling game over (`handle_game_over`).
        -   Team setup (`setup_teams`).
        -   Managing collisions, scores, enemy AI, power-ups.
    -   **`MapService`**: Responsible for creating and generating maps. Can load maps from templates (via `MapRepository`), from map chains, or generate random maps with various parameters (walls, spawns, breakable blocks, enemies).

4.  **Data Access Layer (Repositories - `app/repositories/`)**:
    -   **`NatsRepository`**: Low-level wrapper for interacting with NATS (connection, publishing, subscribing). Used by `EventService`.
    -   **`RedisRepository`**: Wrapper for interacting with Redis (set, get, delete). Used by `MapRepository` for caching.
    -   **`PostgresRepository`**: Wrapper for interacting with PostgreSQL using SQLAlchemy (asynchronous sessions). Used by `MapRepository`.
    -   **`MapRepository`**: Manages storing and retrieving map data (templates, groups, chains). Interacts with PostgreSQL for persistent storage and with Redis for caching.

5.  **Data Models (`app/models/`)**:
    -   **Pydantic models**: Used for data validation in API requests/responses (`MapTemplateCreate`, `MapTemplateUpdate`, etc.) and for game settings (`GameCreateSettings`).
    -   **SQLAlchemy ORM models (`MapTemplateORM`, `MapGroupORM`, `MapChainORM`)**: Define the structure of tables in the PostgreSQL database for storing map information.

6.  **Game Entities (`app/entities/`)**:
    -   Classes representing all game objects: `Player`, `Enemy`, `Bomb`, `Bullet`, `Mine`, `PowerUp`, `Map`, `CellType`, `GameSettings`, `Weapon`, `UnitType`, etc.
    -   They contain the state and basic behavior logic of objects (e.g., `Player.set_inputs()`, `Bomb.update()`).

7.  **Configuration and Utilities**:
    -   `app/config.py`: Loading application settings from environment variables.
    -   `app/logging_config.py`: Configuring the logging system.
    -   `app/auth.py`: Dependency functions for authentication/authorization checks in endpoints.

## Data Flows (simplified)

-   **HTTP Requests (Map Management)**: Client -> `map_routes.py` -> `MapRepository` -> PostgreSQL/Redis.
-   **NATS Commands (Game Actions)**: Client -> NATS -> `EventService` -> `GameCoordinator` -> `GameService` -> `GameModeService` -> Entity updates -> `GameCoordinator` sends `game.update` via `EventService` -> NATS -> Clients.

This architecture aims for loose coupling of components and high extensibility, allowing new game modes, map types, or entities to be added with minimal impact on other parts of the system.
