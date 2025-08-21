# Redis
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/redis/index.md)

## Назначение в проекте

**Redis** — это in-memory хранилище данных, используемое для **кэширования и хранения временных состояний**.

-   **`auth-service`**: Кэширование сессий и токенов.
-   **`game-service`**: Хранение временного состояния активных игр.
-   **`game-allocator-service`**: Отслеживание нагрузки на экземпляры `game-service`.

Для мониторинга используется **`redis-exporter`**, который предоставляет метрики для Prometheus.

## Конфигурация

```yaml
# infra/docker-compose.yml
services:
  redis:
    image: redis:7.2
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

  redis-exporter:
    image: oliver006/redis_exporter:v1.55.0
    environment:
      REDIS_ADDR: redis://redis:6379
    ports: ["9121:9121"]
```

-   **`redis`**: Основной сервис Redis.
-   **`redis-exporter`**: Подключается к основному сервису и предоставляет метрики на порту `9121`.

## Доступ

-   Прямой доступ к Redis возможен по порту `6379`. Через Traefik не маршрутизируется.
