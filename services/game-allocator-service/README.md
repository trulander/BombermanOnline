# Game Allocator Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

The Game Allocator Service is responsible for efficiently allocating game sessions to available game server instances. It uses game server load metrics (CPU and RAM) from Prometheus and consults with Consul to discover healthy instances. The service communicates via NATS to receive game allocation requests and publish results.

## Service Purpose

The main task of the `game-allocator-service` is to ensure load balancing and optimal use of game server resources by intelligently selecting the least loaded instance for a new game session. This is critical for maintaining stable performance and minimizing latency in a multiplayer game.

## Technologies Used

*   **Python 3.9**: Programming language.
*   **`asyncio`**: Asynchronous I/O for high-performance network operations.
*   **NATS**: A lightweight, high-performance messaging system used for asynchronous communication between microservices.
*   **Prometheus API Client (`prometheus-api-client`)**: For programmatically querying load metrics from Prometheus.
*   **Consul (`py-consul`)**: For service discovery and getting a list of healthy game server instances.
*   **Redis (`redis`)**: Used as a cache to store information about allocated game instances (GameInstanceCache).
*   **Pydantic (`pydantic`, `pydantic-settings`)**: For data validation and configuration management.
*   **Python JSON Logger (`python-json-logger`)**: For structured logging.
*   **UV**: A Python package manager used to install dependencies.

## Project Structure

```
services/game-allocator-service/
├── app/
│   ├── __init__.py
│   ├── config.py             # Service configuration settings
│   ├── game_cache.py         # Caching logic for game instances in Redis
│   ├── logging_config.py     # Logging configuration
│   ├── main.py               # Main service logic and entry point
│   ├── nats_repository.py    # Interaction with NATS
│   └── redis_repository.py   # Interaction with Redis
├── Dockerfile                # Docker image definition for the service
├── pyproject.toml            # Project dependency management (via Poetry/uv)
├── README.md                 # General information about the service
└── uv.lock                   # uv dependency lock file
```

## NATS Events and API Endpoints

The `game-allocator-service` primarily communicates through NATS events. It subscribes to requests and publishes responses.

### Requests

*   **`game.assign.request`**:
    *   **Description**: A request to allocate a new game session to a game server.
    *   **Sender**: Typically `webapi-service` or another service initiating a new game.
    *   **Payload (JSON)**:

        ```json
        {
            "game_id": "<game ID>",
            "settings": {
                "resource_level": "low" | "high" // Determines whether to consider CPU (low) or RAM (high) when selecting a server
            }
        }
        ```

### Responses

After processing a `game.assign.request`, the service publishes a response to the subject specified in the `msg.reply` of the NATS message.

*   **Payload (JSON)**:

    ```json
    {
        "success": true | false,
        "instance_id": "<IP address or ID of the game server instance>" // On successful allocation
    }
    ```

## Interaction with Other Services

*   **Consul**: Used to discover all registered `game-service` instances and check their health.
*   **Prometheus**: Queries load metrics (CPU, RAM) for each `game-service` instance to make allocation decisions.
*   **Redis**: Used as a cache to temporarily store the association between `game_id` and `instance_id` (the game server's IP address).
*   **NATS**: The primary communication channel for receiving game allocation requests and sending responses.
*   **Game Service**: The target service to which `game-allocator-service` allocates games. Interaction is indirect, through Consul and Prometheus for monitoring, and through NATS for notifications (although in the current version, NATS notifications are commented out).

## Environment Variables

The service configuration is managed through environment variables defined in `app/config.py`.

*   `SERVICE_NAME`: The name of the service, default `game-allocator-service`.
*   `APP_TITLE`: The application title, default `Bomberman Game Allocator Service`.
*   `GAME_CACHE_TTL`: The cache TTL for game instances in seconds, default `60`.
*   `REDIS_HOST`: Redis host, default `localhost`.
*   `REDIS_PORT`: Redis port, default `6379`.
*   `REDIS_DB`: Redis database, default `0`.
*   `REDIS_PASSWORD`: Password for Redis (optional).
*   `NATS_URL`: NATS server URL, default `nats://localhost:4222`.
*   `PROMETHEUS_URL`: Prometheus server URL, default `http://prometheus:9090`.
*   `CONSUL_HOST`: Consul host, default `consul`.
*   `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL), default `DEBUG`.
*   `LOG_FORMAT`: Logging format (`text` or `json`), default `text`.
*   `TRACE_CALLER`: Whether to include caller information in logs, default `True`.

## Startup and Deployment Instructions

### Local Launch (with Docker Compose)

1.  **Ensure Docker and Docker Compose are installed.**
2.  **Start all necessary infrastructure services via Docker Compose**: Navigate to the project's root directory (`BombermanOnline`) and run:
    ```bash
    docker-compose -f infra/docker-compose.yml up -d
    ```
    This will start Consul, Prometheus, NATS, Redis, and other services that `game-allocator-service` depends on.
3.  **Build and run `game-allocator-service`**: Go to the service directory:
    ```bash
    cd services/game-allocator-service
    ```
    Then build the Docker image and run the container. The `Dockerfile` uses `uv` to install dependencies and run the application.
    ```bash
    docker build -t game-allocator-service .
    docker run --network bombermanonline_default game-allocator-service
    ```
    *(Note: The `bombermanonline_default` network is created when `infra/docker-compose.yml` is launched)*

### Development Mode Launch (without Docker)

1.  **Install Python 3.9 and UV.**
2.  **Install dependencies**: Go to the `services/game-allocator-service` directory and run:
    ```bash
    uv sync
    ```
3.  **Start the service**: Ensure that all necessary external services (Consul, Prometheus, NATS, Redis) are running and accessible from your host. Then run:
    ```bash
    uv run app/main.py
    ```

### Deployment

The service is designed for deployment in a containerized environment (e.g., Docker, Kubernetes). The `Dockerfile` provides everything needed to create a portable image. It is important to ensure that the environment variables are configured correctly for the production environment, especially `CONSUL_HOST`, `PROMETHEUS_URL`, `NATS_URL`, and `REDIS_HOST`.