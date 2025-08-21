# Redis Exporter
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/redis-exporter/index.md)

## Purpose

Exports Redis metrics for Prometheus.

## Configuration

```yaml
# infra/docker-compose.yml
services:
  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    environment:
      REDIS_ADDR: redis://redis:6379
    ports: ["9121:9121"]
```

- **`image`**: `oliver006/redis_exporter:v1.55.0`
- **`environment`**:
  - `REDIS_ADDR`: Specifies the address to connect to Redis.
- **`ports`**: `9121:9121` - the port for Prometheus to scrape metrics.