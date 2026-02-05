# Traefik
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/traefik/index.md)

## Purpose in the Project

**Traefik** is an API Gateway and reverse proxy that serves as the single entry point for all HTTP requests into the system. It is responsible for routing requests to the appropriate microservices, managing SSL certificates (in production), and applying middleware.

## Configuration from docker-compose.yml

```yaml
services:
  traefik:
    image: traefik:3.6.6
    ports:
      - "3000:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - ./traefik/traefik.yml:/etc/traefik/traefik.yml
      - ./traefik/middlewares.yml:/etc/traefik/middlewares.yml
      - ./traefik/routers.yml:/etc/traefik/routers.yml
      - ./traefik/logs:/var/log/traefik
      - ./traefik/traefik_plugins:/plugins-storage
      - ./traefik/local-plugins:/plugins-local/src
    command:
      - "--configFile=/etc/traefik/traefik.yml"
    labels:
      - "traefik.enable=true"
```

-   **`image`**: `traefik:3.6.6` - The Traefik image being used.
-   **`ports`**: Exposes ports `3000` (for HTTP traffic) and `8080` (for the dashboard) to the host machine.
-   **`volumes`**:
    -   `/var/run/docker.sock`: Allows Traefik to automatically discover other containers.
    -   `./traefik/...`: Mounts all necessary configuration files (main, middleware, routers) and directories for logs and plugins.
-   **`command`**: Tells Traefik to use the main configuration file `traefik.yml`.
-   **`labels`**: `traefik.enable=true` enables processing for Traefik itself to allow access to its dashboard.

## Interaction with Other Services

-   **Providers**: Traefik uses three providers to discover routes: `docker` (for services with labels), `file` (to read `routers.yml` and `middlewares.yml`), and `consulCatalog` (for services registered in Consul).
-   **Auth Service**: Uses `auth-service` via the `auth-check` middleware to protect endpoints. Traefik forwards the request to `auth-service`, and if it returns a `200 OK` status, the request is allowed to proceed.
-   **`extractCookie` Local Plugin**: Used for WebSocket authorization. It extracts the token from the `ws_auth_token` cookie and places it into the `Authorization` header.
-   **Microservices**: Routes requests to all public services (`web-frontend`, `webapi-service`, `auth-service`, etc.) according to the rules in `routers.yml`.
-   **Infisical**: Routes the Infisical UI using the `infisical.localhost` host rule.

## Routed Services (Traefik)

The following routes are configured in `infra/traefik/routers.yml`:

-   **Web Frontend**: `/`
-   **WebAPI REST**: `/webapi`
-   **WebAPI WebSocket**: `/webapi/socket.io`
-   **WebAPI Docs**: `/webapi/docs`
-   **Auth Service**: `/auth`
-   **Auth Docs**: `/auth/docs`
-   **Game Service REST**: `/games`
-   **Game Service Docs**: `/games/docs`
-   **Game Service gRPC**: `/games/grpc`
-   **AI Service gRPC**: `/ai/grpc`
-   **Log Collector**: `/logs` (Fluent Bit logger API)
-   **Grafana**: `/grafana`
-   **pgAdmin**: `/pgadmin`
-   **Traefik Dashboard**: `traefik.localhost`
-   **Infisical UI**: `infisical.localhost`

The following routes are configured via Docker labels in `infra/docker-compose.yml`:

-   **Prometheus**: `prometheus.localhost`

## Access

-   **Main Website**: `http://localhost/`
-   **WebAPI**: `http://localhost/webapi/`
-   **WebAPI Docs**: `http://localhost/webapi/docs`
-   **Auth**: `http://localhost/auth/`
-   **Auth Docs**: `http://localhost/auth/docs`
-   **Game Service**: `http://localhost/games/`
-   **Game Service Docs**: `http://localhost/games/docs`
-   **Grafana**: `http://localhost/grafana`
-   **pgAdmin**: `http://localhost/pgadmin`
-   **Prometheus**: `http://prometheus.localhost`
-   **Logs**: `http://localhost/logs`
-   **Infisical UI**: `http://infisical.localhost:3000`
-   **Traefik Dashboard**: `http://traefik.localhost` (also available at `http://localhost:8080`).
