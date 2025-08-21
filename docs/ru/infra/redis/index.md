# Redis
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/redis/index.md)

## Назначение

**Redis** — это in-memory хранилище данных, используемое для **кэширования и хранения временных состояний**.

-   **`auth-service`**: Кэширование сессий и токенов.
-   **`game-service`**: Хранение временного состояния активных игр.
-   **`game-allocator-service`**: Отслеживание нагрузки на экземпляры `game-service`.

## Конфигурация из docker-compose.yml

```yaml
services:
  redis:
    image: redis:7.2
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
```

- **`image`**: `redis:7.2`
- **`ports`**: `6379:6379` - стандартный порт Redis.
- **`volumes`**: `redis_data` - том для сохранения данных.

## Взаимодействие с другими сервисами

-   **Микросервисы**: Все основные сервисы (`auth`, `game`, `webapi` и др.) подключаются к Redis по имени хоста `redis` и порту `6379`.
-   **Redis Exporter**: Сервис `redis-exporter` подключается к Redis для сбора метрик и передачи их в Prometheus.

## Доступность

-   Прямой доступ к Redis доступен на порту `6379`. Он не маршрутизируется через traefik.
