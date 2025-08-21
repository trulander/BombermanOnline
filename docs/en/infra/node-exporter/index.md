# Node Exporter
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/node-exporter/index.md)

## Purpose

Exports host system metrics (CPU, RAM, disk) for Prometheus.

## Configuration

```yaml
# infra/docker-compose.yml
services:
  node-exporter:
    image: prom/node-exporter:v1.7.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.rootfs=/rootfs'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    ports:
      - "9100:9100"
```

- **`image`**: `prom/node-exporter:v1.7.0`
- **`volumes`**: Mounts host system directories to collect metrics.
- **`command`**: Specifies the paths to system directories inside the container.
- **`ports`**: `9100:9100` - the port for Prometheus to scrape metrics.