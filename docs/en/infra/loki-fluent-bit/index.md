# Loki and Fluent Bit
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/loki-fluent-bit/index.md)

## Purpose in the Project

**Loki** and **Fluent Bit** together form the centralized log collection and storage system.

-   **Fluent Bit**: Acts as a lightweight **log collection agent**. It gathers logs from various sources, parses them, enriches them with metadata, and forwards them to storage.
-   **Loki**: Is the **log storage system**. Unlike traditional systems, Loki indexes only the metadata (labels) and not the full text of the messages, which makes it very fast and resource-efficient.

## Fluent Bit Configuration

The configuration is located in `infra/fluent-bit/`:

-   **`fluent-bit.conf`**: The main file defining the log processing pipeline.
-   **`parsers.conf`**: Defines parsing rules for different log formats.

### Log Sources (`fluent-bit.conf`)

1.  **Docker Containers**:
    -   An `[INPUT]` with `Name` = `forward` accepts logs from the Docker daemon on port `24224`.
    -   Logs are parsed as JSON (`Parser json`).
    -   An `[OUTPUT]` sends these logs to Loki with the label `job=docker` and a dynamic label containing the container name (`Label_Keys $container_name`).

2.  **Frontend Application**:
    -   An `[INPUT]` with `Name` = `http` accepts logs from the `web-frontend` on port `8888`.
    -   A `[Filter]` with `Name` = `lua` is used to process log batches.
    -   An `[OUTPUT]` sends these logs to Loki with the labels `job=web-frontend` and `component=frontend`.

## Loki Configuration

The configuration is located in `infra/loki/loki-config.yml`.

-   **`auth_enabled: false`**: Authentication is disabled.
-   **`server.http_listen_port: 3100`**: Loki listens for requests on this port.
-   **`storage_config`**: Configured to store indexes and log chunks on the `filesystem` within the `loki_data` Docker volume.
-   **`schema_config`**: Uses the `v13` schema with a `tsdb` store.

## Interaction

1.  All microservices launched via `docker-compose` are configured to use `fluentd` as the log driver, which sends their logs to port `24224`.
2.  `fluent-bit` receives these logs, as well as logs from the frontend via HTTP.
3.  `fluent-bit` processes and forwards all logs to `Loki`.
4.  `Grafana` is connected to `Loki` as a data source and is used to visualize, search, and analyze the logs.
