# Fluent Bit
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/fluent-bit/index.md)

## Purpose

A log collector and forwarder.

## Configuration

```yaml
# infra/docker-compose.yml
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

- **`image`**: `grafana/fluent-bit-plugin-loki:latest`
- **`volumes`**: Mounts configuration files and the Docker socket.
- **`ports`**: `24224` for logs from Docker, `8888` for logs from the frontend.
- **`environment.LOKI_URL`**: The address for sending logs to Loki.