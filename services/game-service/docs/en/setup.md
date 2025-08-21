[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/setup.md)

# Game Service Setup and Launch

This section describes the steps to install dependencies, configure the environment, and run the Game Service.

## Requirements

-   Python 3.12
-   UV (Python package manager)
-   Docker (for running in a container or for dependencies)
-   Access to PostgreSQL, Redis, and NATS instances.

## Installing Dependencies

The `uv` package manager is used to install dependencies.

1.  **Install UV (if not already installed):**
    ```bash
    pip install uv
    ```

2.  **Create and activate a virtual environment (recommended):**
    In the `services/game-service` root directory:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # for Linux/macOS
    # .venv\Scripts\activate    # for Windows
    ```

3.  **Install project dependencies:**
    While in the `services/game-service` directory (with `.venv` activated):
    ```bash
    uv sync .
    ```
    This command will install all dependencies specified in `pyproject.toml`.

## Environment Configuration

The service is configured using environment variables.

1.  Copy the example file `.env-example` to a new file `.env` in the `services/game-service` directory:
    ```bash
    cp .env-example .env
    ```
2.  Edit the `.env` file, specifying the actual connection parameters for PostgreSQL, Redis, NATS, and other necessary settings.

    **Key variables:**
    -   `POSTGRES_HOST`, `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`
    -   `REDIS_HOST`, `REDIS_PORT`, `REDIS_DB`, `REDIS_PASSWORD`
    -   `NATS_URL`
    -   `PORT` (the port on which the service will run, default 5002)
    -   `LOG_LEVEL`, `LOG_FORMAT`

    A complete list of variables and their default values can be found in `app/config.py`.

## Database Migrations

Before the first launch of the application or after changes to the database models, you need to apply Alembic migrations.

From the `services/game-service` directory:
```bash
uv run python app/manage.py migrate
```

To create new migrations after changing the `MapTemplateORM`, `MapGroupORM`, `MapChainORM` models in `app/models/map_models.py`:
```bash
uv run python app/manage.py makemigrations "<migration_name>"
```

## Running the Service

### For Development (locally)

1.  Ensure that all dependent services (PostgreSQL, Redis, NATS) are running and accessible according to the settings in `.env`.
2.  Apply migrations (see above).
3.  Run the application using Uvicorn for automatic reloading on code changes:
    From the `services/game-service` directory:
    ```bash
    uv run uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-5002} --reload
    ```
    (where `${PORT:-5002}` uses the value from `.env` or 5002 by default).

    The service will be available at `http://localhost:<PORT>`. The API documentation (Swagger UI) will be at `http://localhost:<PORT>/games/docs`.

### Using Docker

Detailed instructions for building and running the Docker image are provided in the main [README.md](../../README.md) of the service.

**Main steps:**

1.  **Build the image:**
    In the `services/game-service` directory:
    ```bash
    docker build -t bomberman-game-service .
    ```

2.  **Run the container:**
    You need to pass environment variables, for example, via `--env-file` or individually via `-e`.
    ```bash
    docker run -p 5002:5002 --env-file .env bomberman-game-service
    ```
    Ensure that the Docker container has access to PostgreSQL, Redis, and NATS (e.g., they are in the same Docker network, and the hosts in `.env` are specified accordingly).

### Using Docker Compose (Recommended for complex launches)

To manage all project services (including Game Service, databases, NATS, etc.), it is recommended to use the `docker-compose.yml` from the `BombermanOnline` project root directory. This simplifies the launch and management of inter-service dependencies.

If `docker-compose.yml` is configured correctly, you can start all services with the command:
```bash
docker-compose up -d
```
To start only the game-service (if it is defined as a service in `docker-compose.yml`):
```bash
docker-compose up -d game-service
```
The configuration for Game Service in `docker-compose.yml` should include building from its `Dockerfile` and passing the necessary environment variables, as well as network configuration.
