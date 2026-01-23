# Game Allocator Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

The Game Allocator Service is responsible for efficiently distributing game sessions among available game server instances. It uses game server load metrics (CPU and RAM) obtained from Prometheus and consults Consul for healthy instance discovery. The service interacts via NATS to receive game allocation requests and to publish results.

## Service Purpose

The main task of the `game-allocator-service` is to ensure load balancing and optimal utilization of game server resources by intelligently selecting the least loaded instance for a new game session. This is critically important for maintaining stable performance and minimizing latency in multiplayer games.

## Technologies Used

*   **Python 3.9**: Programming language.
*   **`asyncio`**: Asynchronous I/O for high-performance network operations.
*   **NATS**: Lightweight, high-performance messaging system used for asynchronous communication between microservices.
*   **Prometheus API Client (`prometheus-api-client`)**: For programmatically querying load metrics from Prometheus.
*   **Consul (`py-consul`)**: For service discovery and obtaining a list of healthy game server instances.
*   **Redis (`redis`)**: Used as a cache to store information about allocated game instances (GameInstanceCache).
*   **Pydantic (`pydantic`, `pydantic-settings`)**: For data validation and configuration management.
*   **Python JSON Logger (`python-json-logger`)**: For structured logging.
*   **UV**: Python package manager used for dependency installation.

## Project Structure

```
services/game-allocator-service/
├── app/
│   ├── __init__.py
│   ├── config.py             # Service configuration settings
│   ├── game_cache.py         # Game instance caching logic in Redis
│   ├── logging_config.py     # Logging configuration
│   ├── main.py               # Main service logic and entry point
│   ├── nats_repository.py    # NATS interaction
│   └── redis_repository.py   # Redis interaction
├── Dockerfile                # Docker image definition for the service
├── pyproject.toml            # Project dependency management (via Poetry/uv)
├── README.md                 # General service information
└── uv.lock                   # uv dependency lock file
```

## NATS Events and API Endpoints

The `game-allocator-service` primarily interacts via NATS events. It subscribes to requests and publishes responses.

### Requests

*   **`game.assign.request`**:
    *   **Description**: Request to allocate a new game session to a game server.
    *   **Sender**: Typically `webapi-service` or another service initiating a new game.
    *   **Payload (JSON)**:

        ```json
        {
            "game_id": "<Game ID>",
            "settings": {
                "resource_level": "low" | "high" // Determines whether to consider CPU (low) or RAM (high) when selecting a server
            }
        }
        ```

*   **`game.instances.request`**:
    *   **Description**: Request to get a list of all healthy `Game Service` instances.
    *   **Sender**: Typically `webapi-service` when it needs to aggregate data from all game service instances (e.g., when getting a list of all games).
    *   **Payload (JSON)**: Empty object `{}`

### Responses

After processing the `game.assign.request`, the service publishes a response to the topic specified in the `msg.reply` of the NATS message.

*   **Payload (JSON)**:

    ```json
    {
        "success": true | false,
        "instance_id": "<IP address or ID of the game server instance>" // Upon successful allocation
    }
    ```

After processing the `game.instances.request`, the service publishes a response to the topic specified in the `msg.reply` of the NATS message.

*   **Payload (JSON)**:

    ```json
    {
        "success": true | false,
        "instances": [
            {
                "address": "<IP address or hostname>",
                "port": 5002
            }
        ] // List of all healthy Game Service instances
    }
    ```

## Interaction with Other Services

*   **Consul**: Used to discover all registered `game-service` instances and check their health.
*   **Prometheus**: Queries load metrics (CPU, RAM) for each `game-service` instance to make allocation decisions.
*   **Redis**: Used as a cache to temporarily store the relationship between `game_id` and `instance_id` (game server IP address).
*   **NATS**: The primary communication channel for receiving game allocation requests and sending responses.
*   **Game Service**: The target service to which `game-allocator-service` allocates games. Interaction is indirect, through Consul and Prometheus for monitoring, and through NATS for notifications (although NATS notifications are commented out in the current version).

## Environment Variables

Service configuration is managed via environment variables defined in `app/config.py`.

*   `SERVICE_NAME`: Service name, default `game-allocator-service`.
*   `APP_TITLE`: Application title, default `Bomberman Game Allocator Service`.
*   `GAME_CACHE_TTL`: Game instance cache time-to-live in seconds, default `60`.
*   `REDIS_HOST`: Redis host, default `localhost`.
*   `REDIS_PORT`: Redis port, default `6379`.
*   `REDIS_DB`: Redis database, default `0`.
*   `REDIS_PASSWORD`: Redis password (optional).
*   `NATS_URL`: NATS server URL, default `nats://localhost:4222`.
*   `PROMETHEUS_URL`: Prometheus server URL, default `http://prometheus:9090`.
*   `CONSUL_HOST`: Consul host, default `consul`.
*   `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL), default `DEBUG`.
*   `LOG_FORMAT`: Logging format (`text` or `json`), default `text`.
*   `TRACE_CALLER`: Whether to include caller information in logs, default `True`.

## Startup and Deployment Instructions

### Local Startup (with Docker Compose)

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Start all necessary infrastructure services via Docker Compose**: Navigate to the project root directory (`BombermanOnline`) and run:
    ```bash
    docker-compose -f infra/docker-compose.yml up -d
    ```
    This will start Consul, Prometheus, NATS, Redis, and other services that `game-allocator-service` depends on.
3.  **Build and run `game-allocator-service`**: Navigate to the service directory:
    ```bash
    cd services/game-allocator-service
    ```
    Then build the Docker image and run the container. The `Dockerfile` uses `uv` to install dependencies and run the application.
    ```bash
    docker build -t game-allocator-service .
    docker run --network bombermanonline_default game-allocator-service
    ```
    *(Note: The `bombermanonline_default` network is created when `infra/docker-compose.yml` is run)*

### Development Mode Startup (without Docker)

1.  **Install Python 3.9 and UV.**
2.  **Install dependencies**: Navigate to the `services/game-allocator-service` directory and run:
    ```bash
    uv sync
    ```
3.  **Start the service**: Ensure all necessary external services (Consul, Prometheus, NATS, Redis) are running and accessible from your host. Then run:
    ```bash
    uv run app/main.py
    ```

### Deployment

The service is designed for deployment in a containerized environment (e.g., Docker, Kubernetes). The `Dockerfile` provides everything needed to create a portable image. It is important to ensure that environment variables are correctly configured for the production environment, especially `CONSUL_HOST`, `PROMETHEUS_URL`, `NATS_URL`, `REDIS_HOST`.
