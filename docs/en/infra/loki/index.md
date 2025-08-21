# Loki
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/loki/index.md)

## Purpose

A log aggregation system.

## Configuration

```yaml
# infra/docker-compose.yml
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

- **`image`**: `grafana/loki:3.5.0`
- **`volumes`**: `loki-config.yml` is the main configuration file; `loki_data` is for log storage.
- **`command`**: Starts Loki with the specified config.
- **`networks`**: Creates the `loki.internal` alias for access from Fluent Bit.