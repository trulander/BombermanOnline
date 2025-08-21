# Loki
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/loki/index.md)

## Purpose

**Loki** is a log aggregation system developed by Grafana. It efficiently stores logs and indexes only their metadata (labels), which ensures high performance.

## Configuration from docker-compose.yml

```yaml
services:
  loki:
    image: grafana/loki:3.5.0
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml -target=all -log.level=info
    networks:
      default:
        aliases:
          - loki.internal
```

-   **`image`**: `grafana/loki:3.5.0`.
-   **`volumes`**: Mounts the `loki-config.yml` configuration file and the `loki_data` volume for log storage.
-   **`command`**: Starts Loki with the specified configuration file.
-   **`ports`**: `3100:3100` - the API port.
-   **`networks.default.aliases`**: Creates the `loki.internal` network alias, which is used by the `fluent-bit` service for reliable log forwarding within the Docker network.

## Interaction with Other Services

-   **Fluent Bit**: Receives log streams from `fluent-bit`.
-   **Grafana**: Serves as a data source for Grafana, which queries and displays the logs.

## Access

-   The service is internal and is not accessed directly via Traefik.
