[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/architecture/repositories.md)

# Data Access Layer (Repositories)

The repository layer in Game Service is responsible for encapsulating the logic for accessing various data sources: PostgreSQL, Redis, and NATS. This allows separating business logic from the implementation details of data storage and retrieval.

## 1. `BaseRepository` (`app/repositories/__init__.py`)

-   **Description**: An abstract base class (Generic ABC) for all repositories. Defines a standard CRUD-like interface that concrete repositories can implement.
-   **Abstract Methods**:
    -   `get(id: str) -> T | None`: Get an object by identifier.
    -   `create(data: T) -> T`: Create a new object.
    -   `update(id: str, data: T) -> T | None`: Update an existing object.
    -   `delete(id: str) -> bool`: Delete an object.
-   **Purpose**: Although defined, in the current codebase, `MapRepository` does not inherit directly from it and implements its own set of methods. Other repositories (`PostgresRepository`, `RedisRepository`, `NatsRepository`) also do not follow this interface, as they provide more specific methods for their data sources.

## 2. `PostgresRepository` (`app/repositories/postgres_repository.py`)

-   **Description**: Provides connection and interaction with the PostgreSQL database using SQLAlchemy in asynchronous mode (`asyncpg` driver).
-   **Key Components and Methods**:
    -   `engine: sa_asyncio.AsyncEngine`: Asynchronous SQLAlchemy engine.
    -   `async_session: sa_asyncio.async_sessionmaker`: Factory for creating asynchronous sessions.
    -   `connect()`: Establishes an asynchronous connection to PostgreSQL, creates the engine and session factory. Executes a test query `SELECT 1` to check the connection.
    -   `disconnect()`: Closes the database connection.
    -   `_ensure_connected()`: Checks the connection status and reconnects if necessary before each operation.
    -   `get_session()`: Asynchronous context manager providing an SQLAlchemy session. Automatically performs `commit` on successful block completion or `rollback` on exception. The session is closed in the `finally` block.
-   **Usage**: Used by `MapRepository` to perform CRUD operations with map ORM models.

## 3. `RedisRepository` (`app/repositories/redis_repository.py`)

-   **Description**: Provides methods for interacting with the Redis server (asynchronously).
-   **Key Components and Methods**:
    -   `_redis: redis.Redis`: Instance of the asynchronous Redis client.
    -   `get_redis()`: Returns an active Redis connection, creating it on the first call or if it was closed. Performs `ping` to check the connection.
    -   `disconnect()`: Closes the Redis connection.
    -   `set(key: str, value: Any, expire: int = 0) -> bool`: Serializes `value` to JSON and saves it to Redis by `key` with an optional `expire` time (in seconds).
    -   `get(key: str) -> Any`: Retrieves the value by `key` from Redis and deserializes it from JSON. Returns `None` if the key is not found.
    -   `delete(key: str) -> bool`: Deletes the key from Redis.
-   **Usage**: Used by `MapRepository` for caching map template, group, and chain data.

## 4. `NatsRepository` (`app/repositories/nats_repository.py`)

-   **Description**: Encapsulates low-level interaction with the NATS server for publishing and subscribing to messages.
-   **Key Components and Methods**:
    -   `_nc: NATS | None`: NATS client instance.
    -   `get_nc()`: Returns an active NATS connection, establishing it if necessary.
    -   `disconnect()`: Gracefully closes the NATS connection (performs `drain`).
    -   `_publish_data(subject: str, payload: dict) -> bool`: Internal method for serializing `payload` to JSON (with NumPy type support) and publishing data with retry logic.
    -   `_send_event_with_reconnect(subject: str, payload_bytes: bytes, max_retries: int = 3, retry_delay: float = 1.0) -> bool`: Sends an event with automatic reconnection and retries in case of failures.
    -   `publish_event(subject_base: str, payload: dict, game_id: Optional[str] = None, specific_suffix: Optional[str] = None) -> bool`: Publishes an event, constructing the subject from the base part, game ID, and suffix.
    -   `publish_simple(subject: str, payload: any) -> bool`: Simplified data publishing.
    -   `subscribe(subject: str, callback)`: Subscribes to the specified NATS subject, calling `callback` upon message reception.
-   **Usage**: Used by `EventService` for all NATS communication.

## 5. `MapRepository` (`app/repositories/map_repository.py`)

-   **Description**: A specialized repository for managing map-related data (templates, groups, chains). It combines the use of PostgreSQL for persistent storage and Redis for caching.
-   **Dependencies**: `PostgresRepository`, `RedisRepository`.
-   **Key Methods (for MapTemplate, similar for MapGroup and MapChain)**:
    -   `create_map_template(template_data: MapTemplateCreate, created_by: str) -> MapTemplate`:
        1.  Creates a new `MapTemplateORM` record in PostgreSQL.
        2.  Converts the ORM object to a Pydantic `MapTemplate` model.
        3.  Caches the Pydantic model (serialized to a dict, with dates in ISO format) in Redis.
    -   `get_map_template(map_id: str) -> Optional[MapTemplate]`:
        1.  Attempts to retrieve data from the Redis cache.
        2.  If not in cache, requests from PostgreSQL (`is_active == True`).
        3.  If found in DB, converts to Pydantic model and caches in Redis.
    -   `update_map_template(map_id: str, template_data: MapTemplateUpdate) -> Optional[MapTemplate]`:
        1.  Updates the record in PostgreSQL.
        2.  Retrieves the updated record from the DB.
        3.  Converts to Pydantic model.
        4.  Updates the cache in Redis.
    -   `delete_map_template(map_id: str) -> bool` (soft delete):
        1.  Sets `is_active = False` in PostgreSQL.
        2.  Deletes the record from the Redis cache.
    -   `list_map_templates(filter_params: MapTemplateFilter) -> List[MapTemplate]`:
        1.  Executes a query to PostgreSQL considering filters (name, difficulty, players, creator) and pagination (`limit`, `offset`).
        2.  Converts the results to a list of Pydantic `MapTemplate` models.
        3.  (Caching for lists is not implemented here).
    -   `get_maps_by_difficulty(min_difficulty: int, max_difficulty: int) -> List[MapTemplate]`: Gets maps by difficulty range.
-   **Caching Logic**: Data is cached in Redis with a TTL (default 1 hour). Cache keys have prefixes (e.g., `map_template:{id}`). Dates are stored in the cache in ISO format and restored upon reading.
