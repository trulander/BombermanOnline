# Redis
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/redis/index.md)

## Purpose in the Project

**Redis** is an in-memory data store used for **caching and storing temporary states**.

-   **`auth-service`**: Caching sessions and tokens.
-   **`game-service`**: Storing the temporary state of active games.
-   **`game-allocator-service`**: Tracking the load on `game-service` instances.

For monitoring, **`redis-exporter`** is used to provide metrics to Prometheus.

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

  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    environment:
      REDIS_ADDR: redis://redis:6379
    ports: ["9121:9121"]
```

-   **`redis`**: The main Redis service.
-   **`redis-exporter`**: Connects to the main service and provides metrics on port `9121`.

## Access

-   Direct access to Redis is available on port `6379`. It is not routed through Traefik.
