# Loki
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/loki/index.md)

## Назначение

Система агрегации логов.

## Конфигурация

```yaml
# infra/docker-compose.yml
services:
  loki:
    image: grafana/loki:3.5.0
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml -target=all -log.level=info
    networks:
      default:
        aliases:
          - loki.internal
```

- **`image`**: `grafana/loki:3.5.0`
- **`volumes`**: `loki-config.yml` - основной файл конфигурации, `loki_data` - хранилище логов.
- **`command`**: Запускает Loki с указанным конфигом.
- **`networks`**: Создает псевдоним `loki.internal` для доступа из Fluent Bit.