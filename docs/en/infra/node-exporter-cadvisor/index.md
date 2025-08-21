# Node Exporter & cAdvisor
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/node-exporter-cadvisor/index.md)

## Purpose in the Project

**Node Exporter** and **cAdvisor** are metrics collection agents that feed data into Prometheus.

-   **`node-exporter`**: Collects metrics from the **host system** where Docker is running (CPU, RAM, disk, network).
-   **`cAdvisor` (Container Advisor)**: Collects performance and resource usage metrics for **each running Docker container**.

These two components provide complete metrics coverage, both at the hardware level and at the individual application level.

## Configuration

Both services are defined in `infra/docker-compose.yml`.

### Node Exporter
```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.7.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
```
-   Mounts host filesystems to collect metrics. Exposes metrics on port `9100`.

### cAdvisor
```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      # ... and other system directories
    ports:
      - "8081:8080"
```
-   Also mounts system directories and the Docker socket. Exposes metrics on port `8080`.

## Access

-   Both services are internal. Prometheus scrapes them directly on ports `9100` and `8080`, respectively.
-   `cAdvisor` has its own web UI for debugging, available at `http://localhost:8081`.
