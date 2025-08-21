# Traefik
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/traefik/index.md)

## Purpose in the Project

**Traefik** is a modern **API Gateway** and **Reverse Proxy** that serves as the single entry point for all HTTP requests into the system.

Key functions in the project:
1.  **Request Routing**: Traefik automatically discovers running services and routes incoming requests to the correct container based on rules defined in `infra/traefik/routers.yml`.
2.  **Consul Integration**: Uses `consulCatalog` to discover services registered in Consul.
3.  **Middleware**: Applies intermediate handlers to requests, configured in `infra/traefik/middlewares.yml`. This includes adding security headers, compression, and handling authentication checks.
4.  **Authentication Check**: Through the `auth-check` middleware, it forwards requests to the `auth-service` to validate JWT tokens before granting access to protected resources.
5.  **WebSocket Authorization**: Uses the `extractCookie` local plugin to extract the `ws_auth_token` from a cookie and pass it in the `Authorization` header to authenticate WebSocket connections.

## Configuration

Traefik's main configuration is split into several files within the `infra/traefik/` directory:

-   **`traefik.yml`**: The main static configuration file. It defines entry points (`web`), providers (`docker`, `file`, `consulCatalog`), logging settings, and enables the dashboard.
-   **`routers.yml`**: Dynamic configuration that defines routing rules (`rule`) for each endpoint, the `entryPoints` used, and `middlewares` chains.
-   **`middlewares.yml`**: Defines all the middleware used.

### Main Routes (`routers.yml`)

-   `/auth/**`: Routes to `auth-service`.
-   `/webapi/**`: Routes to `webapi-service` (protected by `auth-check`).
-   `/webapi/socket.io`: Route for WebSockets, uses `extract-cookie-ws_auth_token` and `auth-check`.
-   `/games/**`: Routes to `game-service` (protected by `auth-check`).
-   `/logs`: Route for receiving logs from the frontend, forwarded to `fluent-bit`.
-   `/`: All other requests are routed to `web-frontend`.

### Key Middlewares (`middlewares.yml`)

-   `security-headers`: Adds standard security headers.
-   `compress`: Enables GZIP compression.
-   `auth-check`: `forwardAuth` to the `http://auth-service:5003/auth/api/v1/auth/check` endpoint for token validation.
-   `extract-cookie-ws_auth_token`: A local plugin that takes the `ws_auth_token` cookie and converts it into an `Authorization: Bearer <token>` header.

## Access via Traefik

-   **Main Website**: `http://localhost/`
-   **API Services**: `http://localhost/auth/`, `http://localhost/webapi/`, `http://localhost/games/`
-   **Traefik Dashboard**: `http://traefik.localhost` (as per `routers.yml`, also available at `http://localhost:8080` from `docker-compose.yml`).
