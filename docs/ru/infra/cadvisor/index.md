# cAdvisor
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/cadvisor/index.md)

## Назначение

Агент для сбора метрик использования ресурсов контейнеров.

## Конфигурация

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
- **`volumes`**: Монтируются системные директории для сбора информации о контейнерах.
- **`ports`**: `8081:8080` - предоставляет собственный веб-интерфейс, Prometheus собирает метрики с порта `8080`.