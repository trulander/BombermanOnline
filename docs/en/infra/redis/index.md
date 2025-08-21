# Redis
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/redis/index.md)

## Purpose

**Redis** is an in-memory data store used for **caching and storing temporary states**.

-   **`auth-service`**: Caching sessions and tokens.
-   **`game-service`**: Storing the temporary state of active games.
-   **`game-allocator-service`**: Tracking the load on `game-service` instances.

## Configuration

```yaml
# infra/docker-compose.yml
services:
  redis:
    image: redis:7.2
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

- **`image`**: `redis:7.2`
- **`ports`**: `6379:6379` - the standard Redis port.
- **`volumes`**: `redis_data` - a volume to persist data.

## Access

-   Direct access to Redis is available on port `6379`. It is not routed through Traefik.
