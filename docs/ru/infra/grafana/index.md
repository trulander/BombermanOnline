# Grafana
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/grafana/index.md)

## Назначение в проекте

**Grafana** — это платформа для **аналитики и интерактивной визуализации**. В проекте она служит единым центром для мониторинга, объединяя метрики из Prometheus и логи из Loki.

## Конфигурация

Автоматическая конфигурация Grafana (provisioning) находится в `infra/grafana/provisioning/`.

-   **`datasources/datasources.yml`**:
    -   Автоматически настраивает два источника данных:
        1.  **`Prometheus`**: `http://prometheus:9090`, установлен как источник по умолчанию.
        2.  **`Loki`**: `http://loki:3100`.

-   **`dashboards/dashboards.yml`**:
    -   Указывает Grafana автоматически загружать все дашборды из директории `/var/lib/grafana/dashboards` (которая монтируется из `infra/grafana/dashboards/`).

## Дашборды

В проекте предустановлены следующие дашборды (`infra/grafana/dashboards/*.json`):

-   **`complete_dashboard.json`**: Общий дашборд, включающий:
    -   **Микросервисы**: RPS и 95-й процентиль задержки для `webapi-service` и `game-service`.
    -   **Система**: Общее использование CPU и памяти хоста.
    -   **Контейнеры**: Использование CPU и памяти по каждому контейнеру.
    -   **Redis**: Команды в секунду и использование памяти.
    -   **Логи**: Панель с последними логами из Loki.

-   **`logs_dashboard.json`**: Специализированный дашборд для логов:
    -   Фильтры по ключевым словам, уровню лога и сервису.
    -   Панель, показывающая только логи с уровнем `ERROR`, `CRITICAL`, `FATAL`, `WARN`.
    -   Графики распределения логов по сервисам и по уровням.
    -   Настроен алерт на критические ошибки.

-   **`microservices.json`**: Дашборд с метриками RPS и задержек для `webapi-service` и `game-service`.

-   **`nats_dashboard.json`**: Метрики NATS, включая количество соединений, использование CPU, скорость обмена сообщениями и трафик.

-   **`redis_dashboard.json`**: Детальные метрики Redis: количество клиентов, throughput, использование памяти, статистика по ключам и попаданиям в кэш.

-   **`socket_dashboard.json`**: Метрики, связанные с WebSocket и NATS, включая активные соединения и игры.

## Доступ

-   **URL**: `http://grafana.localhost` (настроен через Traefik в `docker-compose.yml`).
-   **Логин/Пароль**: `admin`/`admin` (заданы как переменные окружения в `docker-compose.yml`).
