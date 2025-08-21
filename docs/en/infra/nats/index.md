# NATS
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/nats/index.md)

## Purpose

**NATS** is a high-performance **messaging system (message bus)** for asynchronous communication between microservices.

-   **`game-service`** publishes game state change events.
-   **`ai-service`** subscribes to these events and sends AI control commands.
-   **`game-allocator-service`** coordinates the distribution of game sessions.

## Configuration

```yaml
# infra/docker-compose.yml
services:
  nats:
    image: nats:2.10
    ports:
      - "4222:4222"  # Client port
      - "8222:8222"  # Monitoring port
    volumes:
      - nats_data:/data
```

- **`image`**: `nats:2.10`
- **`ports`**: `4222` for clients, `8222` for monitoring.
- **`volumes`**: `nats_data` for data persistence.

## Access

-   The service is internal and is not routed through Traefik.
