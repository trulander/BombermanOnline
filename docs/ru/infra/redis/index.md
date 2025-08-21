# Redis
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/redis/index.md)

## Назначение

**Redis** — это in-memory хранилище данных, используемое для **кэширования и хранения временных состояний**.

-   **`auth-service`**: Кэширование сессий и токенов.
-   **`game-service`**: Хранение временного состояния активных игр.
-   **`game-allocator-service`**: Отслеживание нагрузки на экземпляры `game-service`.

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
```

- **`image`**: `redis:7.2`
- **`ports`**: `6379:6379` - стандартный порт Redis.
- **`volumes`**: `redis_data` - том для сохранения данных.

## Доступ

-   Прямой доступ к Redis возможен по порту `6379`. Через Traefik не маршрутизируется.
