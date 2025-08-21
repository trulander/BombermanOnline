# Node Exporter
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/node-exporter/index.md)

## Назначение

Экспортер метрик хост-системы (CPU, RAM, диск) для Prometheus.

## Конфигурация

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
- **`volumes`**: Монтируются системные директории хоста для сбора метрик.
- **`command`**: Указывает пути к системным директориям внутри контейнера.
- **`ports`**: `9100:9100` - порт для сбора метрик Prometheus.