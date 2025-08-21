# Redis Exporter
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/redis-exporter/index.md)

## Назначение

Экспортер метрик Redis для Prometheus.

## Конфигурация

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
  - `REDIS_ADDR`: Указывает адрес для подключения к Redis.
- **`ports`**: `9121:9121` - порт для сбора метрик Prometheus.