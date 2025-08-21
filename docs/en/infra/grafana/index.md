# Grafana
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/grafana/index.md)

## Purpose in the Project

**Grafana** is a platform for **analytics and interactive visualization**. In this project, it serves as a unified center for monitoring, combining metrics from Prometheus and logs from Loki.

## Configuration

Grafana's automatic configuration (provisioning) is located in `infra/grafana/provisioning/`.

-   **`datasources/datasources.yml`**:
    -   Automatically configures two data sources:
        1.  **`Prometheus`**: `http://prometheus:9090`, set as the default source.
        2.  **`Loki`**: `http://loki:3100`.

-   **`dashboards/dashboards.yml`**:
    -   Tells Grafana to automatically load all dashboards from the `/var/lib/grafana/dashboards` directory (which is mounted from `infra/grafana/dashboards/`).

## Dashboards

The project comes with the following pre-configured dashboards (`infra/grafana/dashboards/*.json`):

-   **`complete_dashboard.json`**: A comprehensive dashboard including:
    -   **Microservices**: RPS and 95th percentile latency for `webapi-service` and `game-service`.
    -   **System**: Overall host CPU and memory usage.
    -   **Containers**: CPU and memory usage per container.
    -   **Redis**: Commands per second and memory usage.
    -   **Logs**: A panel with the latest logs from Loki.

-   **`logs_dashboard.json`**: A specialized dashboard for logs:
    -   Filters for keywords, log level, and service.
    -   A panel showing only logs with level `ERROR`, `CRITICAL`, `FATAL`, `WARN`.
    -   Graphs for log distribution by service and level.
    -   An alert is configured for critical errors.

-   **`microservices.json`**: A dashboard with RPS and latency metrics for `webapi-service` and `game-service`.

-   **`nats_dashboard.json`**: NATS metrics, including connection count, CPU usage, message rate, and traffic.

-   **`redis_dashboard.json`**: Detailed Redis metrics: client count, throughput, memory usage, key statistics, and cache hits.

-   **`socket_dashboard.json`**: Metrics related to WebSockets and NATS, including active connections and games.

## Access

-   **URL**: `http://grafana.localhost` (configured via Traefik in `docker-compose.yml`).
-   **Login/Password**: `admin`/`admin` (set as environment variables in `docker-compose.yml`).
