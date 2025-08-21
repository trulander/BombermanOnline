# Prometheus NATS Exporter
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/prometheus-nats-exporter/index.md)

## Назначение

Экспортер метрик NATS для Prometheus.

## Конфигурация

```yaml
# infra/docker-compose.yml
services:
  prometheus-nats-exporter:
    image: natsio/prometheus-nats-exporter:latest
    command: "-varz -connz -subz -routez -gatewayz -healthz -accstatz -leafz -jsz=all http://nats:8222"
    ports:
      - "7777:7777"
```

- **`image`**: `natsio/prometheus-nats-exporter:latest`
- **`command`**: Указывает адрес мониторингового эндпоинта NATS (`http://nats:8222`).
- **`ports`**: `7777:7777` - порт для сбора метрик Prometheus.