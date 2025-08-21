# Prometheus
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/prometheus/index.md)

## Purpose in the Project

**Prometheus** is a **monitoring and metrics collection** system. It is the central component for gathering performance and health data from all services in the project.

Prometheus periodically scrapes the `/metrics` HTTP endpoints provided by various services and exporters, and stores the collected data in its time-series database. This data is then used by **Grafana** to build graphs and dashboards.

## Configuration

The main configuration file is located at `infra/prometheus/prometheus.yml`.

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # ... other jobs ...
```

### Scrape Targets

According to `prometheus.yml`, metrics are configured to be scraped from the following services and exporters:

-   `prometheus`: itself (localhost:9090)
-   `webapi-service`: `webapi-service:5001` (5s interval)
-   `game-service`: `game-service:5002` (5s interval)
-   `node-exporter`: `node-exporter:9100` (host machine metrics)
-   `cadvisor`: `cadvisor:8080` (Docker container metrics)
-   `redis-exporter`: `redis-exporter:9121` (Redis metrics)
-   `nats-exporter`: `prometheus-nats-exporter:7777` (NATS metrics)
-   `loki`: `loki:3100`
-   `fluent-bit`: `fluent-bit:2020`
-   `grafana`: `grafana:3001`

## Access via Traefik

-   **URL**: `http://prometheus.localhost`
-   This endpoint is configured in `docker-compose.yml` via labels on the `prometheus` service and provides access to the Prometheus web UI for running PromQL queries and checking target status.
