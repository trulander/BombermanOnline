# Prometheus NATS Exporter
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/prometheus-nats-exporter/index.md)

## Purpose

Exports NATS metrics for Prometheus.

## Configuration

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
- **`command`**: Specifies the address of the NATS monitoring endpoint (`http://nats:8222`).
- **`ports`**: `7777:7777` - the port for Prometheus to scrape metrics.