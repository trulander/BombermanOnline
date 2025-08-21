# Grafana
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/grafana/index.md)

## Purpose in the Project

**Grafana** is a platform for data visualization, monitoring, and analysis. It is used as a unified interface to view metrics from Prometheus and logs from Loki.

## Configuration from docker-compose.yml

```yaml
services:
  grafana:
    image: grafana/grafana:12.0.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_HTTP_PORT=3001
      - GF_DASHBOARDS_MIN_REFRESH_INTERVAL=5s
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    ports:
      - "3001:3001"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.localhost`)"
      - "traefik.http.services.grafana.loadbalancer.server.port=3001"
```

-   **`image`**: `grafana/grafana:12.0.0`.
-   **`volumes`**: Mounts directories for Grafana's data and for automatic provisioning of data sources and dashboards.
-   **`environment`**: Sets numerous variables for Grafana's configuration, including:
    -   `GF_SECURITY_ADMIN_USER`/`PASSWORD`: Administrator credentials.
    -   `GF_USERS_ALLOW_SIGN_UP=false`: Disables new user registration.
    -   `GF_AUTH_ANONYMOUS_ENABLED=true`: Allows anonymous access with the `Viewer` role.
-   **`labels`**: Configure Traefik to provide access to Grafana at `grafana.localhost`.

## Interaction with Other Services

-   **Prometheus**: Grafana uses Prometheus as its primary data source for metrics.
-   **Loki**: Uses Loki as a data source for displaying and querying logs.
-   **Provisioning**: On startup, it automatically configures connections to Prometheus and Loki based on files in `./grafana/provisioning/datasources` and loads all dashboards from `./grafana/dashboards`.

## Access

-   **URL**: `http://grafana.localhost` (via Traefik).
-   **Direct Access**: `http://localhost:3001`.
-   **Login/Password**: `admin`/`admin`.