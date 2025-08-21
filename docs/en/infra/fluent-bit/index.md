# Fluent Bit
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/fluent-bit/index.md)

## Purpose

**Fluent Bit** is a lightweight and high-performance log collector and forwarder. It gathers logs from all containers, parses them, and sends them to Loki.

## Configuration from docker-compose.yml

```yaml
services:
  fluent-bit:
    image: grafana/fluent-bit-plugin-loki:latest
    volumes:
      - ./fluent-bit/fluent-bit.conf:/fluent-bit/etc/fluent-bit.conf
      - ./fluent-bit/parsers.conf:/fluent-bit/etc/parsers.conf
      - /var/run/docker.sock:/var/run/docker.sock
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    ports:
      - "24224:24224"
      - "24224:24224/udp"
      - "2020:2020"
      - "8888:8888"
    environment:
      - LOKI_URL=http://loki.internal:3100/loki/api/v1/push
```

-   **`image`**: `grafana/fluent-bit-plugin-loki:latest` - an image with the Loki plugin.
-   **`volumes`**: Mounts configuration files (`fluent-bit.conf`, `parsers.conf`) and the Docker socket to collect container metadata.
-   **`ports`**:
    -   `24224`: Receives logs from Docker containers via the `forward` protocol.
    -   `8888`: Receives logs from the `web-frontend` via HTTP.
    -   `2020`: An HTTP server for monitoring Fluent Bit itself.
-   **`environment.LOKI_URL`**: Specifies the Loki address for sending logs, using the internal network alias `loki.internal`.

## Interaction with Other Services

-   **Docker**: All microservices in `docker-compose.yml` are configured with `logging.driver: "fluentd"`, which directs their `stdout` and `stderr` to Fluent Bit.
-   **Loki**: Is the sole recipient (`output`) of processed logs from Fluent Bit.
-   **Web Frontend**: Sends its logs to port `8888`.

## Access

-   The service is internal and is not accessed directly via Traefik.
