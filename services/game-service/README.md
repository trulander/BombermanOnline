# Game Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

The Game Service is a key component of the Bomberman Online platform, responsible for all game process logic. It manages game creation, player connections, game event processing, game state updates, and interaction with other services.

## Key Features

-   **Game Session Management:** Create, configure, start, pause, and end games via REST API.
-   **Game Mode Support:** Campaign, Free-for-all, Capture the Flag with customizable parameters.
-   **Player Management:** Add/remove players, manage their state, and process input.
-   **Team System:** Create teams, automatic player distribution, scoring system.
-   **Combat System:** Use various types of weapons (bombs, bullets, mines).
-   **Map Management:** Generate random maps, load from templates and chains via REST API.
-   **Artificial Intelligence:** Manage enemies and their behavior.
-   **Power-up System:** Power-ups to improve player characteristics.
-   **Real-time:** Interaction via NATS for asynchronous processing of game events.
-   **REST API:** Full management of games, teams, and maps.
-   **Persistence:** Store map data in PostgreSQL and cache in Redis.
-   **AI Training gRPC:** Separate training mode with `reset/step` without the global game loop.

## Technologies

-   **Programming Language:** Python 3.12
-   **Framework:** FastAPI
-   **Database:** PostgreSQL (for map storage)
-   **Cache:** Redis (for caching map data)
-   **Messaging System:** NATS
-   **ORM/Query Builder:** SQLAlchemy (asynchronous)
-   **Dependency Management and Build:** UV
-   **Database Migrations:** Alembic
-   **Containerization:** Docker
-   **Logging:** python-json-logger

## Installing Dependencies

The `uv` package manager is used to install dependencies.

1.  Make sure you have `uv` installed. If not, install it:
    ```bash
    pip install uv
    ```
2.  Create and activate a virtual environment (recommended):
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # for Linux/macOS
    # .venv\Scripts\activate    # for Windows
    ```
3.  Install dependencies from `pyproject.toml` (while in the `services/game-service` directory):
    ```bash
    uv pip install .
    # or, if dev dependencies are needed and for editable installation:
    # uv pip install -e ".[dev]".
    ```

## Running the Service

### Local Run (for development)

1.  Make sure all necessary services are running: PostgreSQL, Redis, NATS. Their connection configuration is in the `.env` file (create it from `.env-example` if necessary in the `services/game-service` directory).
2.  Apply database migrations:
    From the `services/game-service` directory:
    ```bash
    uv run python app/manage.py migrate
    ```
3.  Start the FastAPI application using Uvicorn:
    From the `services/game-service` directory:
    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
    ```
    The service will be available at `http://localhost:5002`. API documentation (Swagger UI) will be available at `http://localhost:5002/games/docs`.

### API Endpoints

The service provides the following groups of REST API endpoints:

-   **Games (`/games/api/v1/games`):**
    -   `GET /` - Get a list of games with filtering
    -   `GET /{game_id}` - Get detailed game information
    -   `POST /` - Create a new game
    -   `PUT /{game_id}/settings` - Update game settings
    -   `PUT /{game_id}/status` - Change game status (start/pause/resume)
    -   `POST /{game_id}/players` - Add a player to the game
    -   `DELETE /{game_id}/players/{player_id}` - Remove a player from the game
    -   `DELETE /{game_id}` - Delete a game

-   **Teams (`/games/api/v1/teams`):**
    -   `GET /{game_id}` - Get game teams
    -   `POST /{game_id}` - Create a team
    -   `PUT /{game_id}/{team_id}` - Update a team
    -   `DELETE /{game_id}/{team_id}` - Delete a team
    -   `POST /{game_id}/{team_id}/players` - Add a player to a team
    -   `DELETE /{game_id}/{team_id}/players/{player_id}` - Remove a player from a team
    -   `POST /{game_id}/distribute` - Automatically distribute players into teams

-   **Maps (`/games/api/v1/maps`):**
    -   `POST /templates` - Create a map template
    -   `GET /templates` - Get a list of map templates
    -   `GET /templates/{id}` - Get a map template
    -   `PUT /templates/{id}` - Update a map template
    -   `DELETE /templates/{id}` - Delete a map template
    -   Similar operations for groups (`/groups`) and chains (`/chains`) of maps

Detailed API documentation can be found in [docs/en/api_endpoints.md](docs/en/api_endpoints.md).

### Running with Docker

1.  **Build Docker Image:**
    While in the `services/game-service` directory, run:
    ```bash
    docker build -t bomberman-game-service .
    ```
2.  **Run Docker Container:**
    (Example, requires running PostgreSQL, Redis, NATS and appropriate Docker network configuration. Environment variables can be passed via `-e` or a file)
    ```bash
    docker run -p 5002:5002 \
           --env-file .env \ # Make sure .env file is configured for Docker environment
           bomberman-game-service
    ```
    For a full Docker run, it is recommended to use `docker-compose.yml` from the project root directory, which manages all services and their configurations.

## Environment Variables

The service is configured using environment variables. An example file with environment variables can be found in `services/game-service/.env-example`. This file can be imported into Infisical as a base configuration for secrets. Key variables:

-   `API_V1_STR`: Prefix for API V1.
-   `HOST`, `PORT`: Host and port for FastAPI.
-   `DEBUG`, `RELOAD`: Debug and reload flags for Uvicorn.
-   `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`: PostgreSQL connection settings.
-   `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`: Redis connection settings.
-   `NATS_URL`: URL for connecting to NATS.
-   `AI_SERVICE_GRPC_HOST`, `AI_SERVICE_GRPC_PORT`: ai-service gRPC address for AI inference.
-   `LOG_LEVEL`, `LOG_FORMAT`, `TRACE_CALLER`: Logging settings.
-   `GAME_UPDATE_FPS`: Game loop update frequency (frames per second).
-   `AI_ACTION_INTERVAL`: Interval between AI inference requests (seconds).

## Secrets Management

Secrets are managed in Infisical. The Docker entrypoint logs in to Infisical using the `INFISICAL_*` variables and runs the service with injected environment variables. The `.env-example` file can be imported into Infisical to bootstrap the configuration.

## AI Training gRPC

-   `Reset` creates a standalone training game and returns `session_id` and observation.
-   `Step` advances the game by `delta_seconds` (default 0.33 sec) and returns observation, `reward`, `terminated`, `truncated`.
-   Training games are not included in the common list and do not use the global game loop.
-   Entities with `ai=True` trigger inference calls to `ai-service` in the classic loop.

## Postman

Файлы для импорта в Postman находятся в `services/game-service/postman`:

- `game-service-rest.postman_collection.json` — REST эндпоинты
- `game-service.postman_environment.json` — окружение- `bomberman_ai.proto` — gRPC контракт для Postman

See `app/config.py` for a complete list and default values.

## Project Structure

-   `app/`: Main application code.
    -   `alembic/`: Alembic database migrations.
    -   `auth.py`: Authentication/authorization functions.
    -   `coordinators/`: Coordinators managing complex logic (e.g., `GameCoordinator`).
    -   `entities/`: Classes representing game entities.
    -   `main.py`: FastAPI application entry point, initialization.
    -   `manage.py`: CLI for management (e.g., migrations).
    -   `models/`: Pydantic models for API and SQLAlchemy ORM models.
    -   `repositories/`: Classes for data access.
    -   `routes/`: API endpoints.
    -   `services/`: Business logic, game modes.
    -   `config.py`: Application configuration from environment variables.
    -   `logging_config.py`: Logging configuration.
-   `docs/`: Detailed service documentation.
-   `Dockerfile`: Instructions for building the Docker image.
-   `pyproject.toml`: Project description and its dependencies.
-   `README.md`: This file.
-   `.env-example`: Example environment variables file.

## Additional Documentation

More detailed information about service components, API, events, and architecture can be found in the [docs/en](./docs/en) directory.

### API Endpoints
- [Game Service API Endpoints](docs/en/api_endpoints.md)

### Architecture
- [Game Entities](docs/en/architecture/entities.md)
- [Data Models](docs/en/architecture/models.md)
- [Game Service Architecture Overview](docs/en/architecture/overview.md)
- [Data Access Layer (Repositories)](docs/en/architecture/repositories.md)
- [Service Layer](docs/en/architecture/services.md)

### Configuration
- [Game Service Configuration](docs/en/configuration.md)

### Diagrams
- [REST API Endpoints Diagram](docs/en/diagrams/api_endpoints_diagram.md)
- [Class Diagram (Core Entities)](docs/en/diagrams/class_diagram.md)
- [Sequence Diagram: `game.input` Processing](docs/en/diagrams/nats_game_input_sequence_diagram.md)

### Introduction
- [Introduction to Game Service](docs/en/introduction.md)

### NATS Events
- [Game Service NATS Events](docs/en/nats_events.md)

### Player Commands and Their Processing
- [Player Commands and Their Processing](docs/en/player_commands_and_actions.md)

### Installation and Startup
- [Game Service Installation and Startup](docs/en/setup.md)

### Team Logic
- [Team Logic (Teams)](docs/en/teams_logic.md)
