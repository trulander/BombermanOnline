# Fluent Bit
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/fluent-bit/index.md)

## Назначение

Сборщик и пересыльщик логов.

## Конфигурация

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
- **`volumes`**: Подключаются файлы конфигурации и сокет Docker.
- **`ports`**: `24224` для логов от Docker, `8888` для логов от фронтенда.
- **`environment.LOKI_URL`**: Адрес для отправки логов в Loki.