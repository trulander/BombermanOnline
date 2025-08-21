# cAdvisor
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/cadvisor/index.md)

## Purpose

An agent for collecting container resource usage metrics.

## Configuration

```yaml
# infra/docker-compose.yml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    ports:
      - "8081:8080"
```

- **`image`**: `gcr.io/cadvisor/cadvisor:v0.47.2`
- **`volumes`**: Mounts system directories to collect information about containers.
- **`ports`**: `8081:8080` - exposes its own web UI; Prometheus scrapes metrics from port `8080`.