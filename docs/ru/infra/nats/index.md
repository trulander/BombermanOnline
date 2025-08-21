# NATS
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/nats/index.md)

## Назначение в проекте

**NATS** — это высокопроизводительная **система обмена сообщениями (message bus)** для асинхронного взаимодействия между микросервисами.

-   **`game-service`** публикует события об изменении состояния игры.
-   **`ai-service`** подписывается на эти события и отправляет команды управления AI.
-   **`game-allocator-service`** координирует распределение игровых сессий.

Для мониторинга используется **`prometheus-nats-exporter`**.

## Конфигурация

```yaml
# infra/docker-compose.yml
services:
  nats:
    image: nats:2.10
    ports:
      - "4222:4222"  # Клиентский порт
      - "8222:8222"  # Порт для мониторинга
    volumes:
      - nats_data:/data

  prometheus-nats-exporter:
    image: natsio/prometheus-nats-exporter:latest
    command: "-varz -connz -subz -routez -gatewayz -healthz -accstatz -leafz -jsz=all http://nats:8222"
    ports:
      - "7777:7777"
```

-   **`nats`**: Основной сервер NATS.
-   **`prometheus-nats-exporter`**: Собирает метрики с мониторингового порта `8222` и отдает их Prometheus на порту `7777`.

## Доступ

-   Сервис является внутренним и не маршрутизируется через Traefik.
