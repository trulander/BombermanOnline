# Consul
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/consul/index.md)

## Purpose in the Project

**Consul** is used in the project as a key component for **Service Discovery**.

Microservices (`webapi-service`, `game-service`, `auth-service`, `game-allocator-service`, `ai-service`, etc.) register with Consul upon startup. This allows them to find each other by service name (e.g., `auth-service`) instead of hard-coded IP addresses, which is critical for a distributed system. Traefik also uses Consul (via the `consulCatalog` provider) to dynamically discover backends.

All services register with Consul using HTTP healthcheck endpoints (e.g., `/health`), allowing Consul to automatically check instance health and exclude non-working instances from available ones.

## Configuration

The `consul` service is defined in the `infra/docker-compose.yml` file:

```yaml
services:
  consul:
    image: hashicorp/consul:1.21
    ports:
      - "8500:8500"      # HTTP UI and API
      - "8600:8600/udp"  # DNS interface
    command: "agent -server -bootstrap-expect=1 -ui -client=0.0.0.0"
```

-   **`image`**: `hashicorp/consul:1.21`.
-   **`ports`**:
    -   `8500:8500`: Web UI and HTTP API.
    -   `8600:8600/udp`: DNS port for resolving service names.
-   **`command`**: Starts Consul in a single-server mode with the UI enabled.

## Access

-   **Consul Web UI**: `http://localhost:8500`
-   The service is not exposed externally via Traefik as it is an internal component.
