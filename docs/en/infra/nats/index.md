# NATS
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/nats/index.md)

## Purpose in the Project

**NATS** is a high-performance **messaging system (message bus)** for asynchronous communication between microservices.

-   **`game-service`** publishes game state change events.
-   **`ai-service`** subscribes to these events and sends AI control commands.
-   **`game-allocator-service`** coordinates the distribution of game sessions.

For monitoring, **`prometheus-nats-exporter`** is used.

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

  prometheus-nats-exporter:
    image: natsio/prometheus-nats-exporter:latest
    command: "-varz -connz -subz -routez -gatewayz -healthz -accstatz -leafz -jsz=all http://nats:8222"
    ports:
      - "7777:7777"
```

-   **`nats`**: The main NATS server.
-   **`prometheus-nats-exporter`**: Scrapes metrics from the monitoring port `8222` and exposes them to Prometheus on port `7777`.

## Access

-   The service is internal and is not routed through Traefik.
