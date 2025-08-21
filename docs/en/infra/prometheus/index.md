# Prometheus
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/prometheus/index.md)

## Purpose in the Project

**Prometheus** is a monitoring system responsible for collecting and storing metrics as time-series data. It serves as the central data store for Grafana.

## Configuration from docker-compose.yml

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.49.1
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.localhost`)"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
```

-   **`image`**: `prom/prometheus:v2.49.1`.
-   **`volumes`**:
    -   `./prometheus/prometheus.yml`: The main configuration file where scrape targets are defined.
    -   `prometheus_data`: A volume for storing the time-series database.
-   **`command`**: Sets configuration flags, including the path to the config and database.
-   **`ports`**: `9090:9090` - the port for accessing the Prometheus web UI.
-   **`labels`**: Configure Traefik to provide access to the dashboard at `prometheus.localhost`.

## Interaction with Other Services

-   **Exporters**: Prometheus actively scrapes the `/metrics` endpoints of numerous services defined in `prometheus.yml`:
    -   `node-exporter` (host metrics)
    -   `cadvisor` (container metrics)
    -   `redis-exporter` (Redis metrics)
    -   `prometheus-nats-exporter` (NATS metrics)
    -   As well as the application services themselves: `webapi-service`, `game-service`, `loki`, `fluent-bit`, `grafana`.
-   **Grafana**: Serves as a data source for Grafana, which queries the data using PromQL and visualizes it.

## Access

-   **URL**: `http://prometheus.localhost` (via Traefik).
-   **Direct Access**: `http://localhost:9090`.
