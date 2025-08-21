# Prometheus
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/prometheus/index.md)

## Назначение в проекте

**Prometheus** — это система мониторинга, отвечающая за сбор и хранение метрик в виде временных рядов. Она является центральным хранилищем данных для Grafana.

## Конфигурация из docker-compose.yml

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.49.1
    volumes:
      - ./prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--web.enable-lifecycle'
    ports:
      - "9090:9090"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.prometheus.rule=Host(`prometheus.localhost`)"
      - "traefik.http.services.prometheus.loadbalancer.server.port=9090"
```

-   **`image`**: `prom/prometheus:v2.49.1`.
-   **`volumes`**:
    -   `./prometheus/prometheus.yml`: Основной конфигурационный файл, где определены цели для сбора метрик (`scrape_configs`).
    -   `prometheus_data`: Том для хранения базы данных временных рядов.
-   **`command`**: Задает конфигурационные флаги, включая путь к конфигу и базе данных.
-   **`ports`**: `9090:9090` - порт для доступа к веб-интерфейсу Prometheus.
-   **`labels`**: Настраивают Traefik для предоставления доступа к дашборду по адресу `prometheus.localhost`.

## Взаимодействие с другими сервисами

-   **Экспортеры**: Prometheus активно опрашивает (`scrape`) эндпоинты `/metrics` у множества сервисов, определенных в `prometheus.yml`:
    -   `node-exporter` (метрики хоста)
    -   `cadvisor` (метрики контейнеров)
    -   `redis-exporter` (метрики Redis)
    -   `prometheus-nats-exporter` (метрики NATS)
    -   А также метрики самих сервисов: `webapi-service`, `game-service`, `loki`, `fluent-bit`, `grafana`.
-   **Grafana**: Служит источником данных для Grafana, которая запрашивает данные с помощью языка PromQL и визуализирует их.

## Доступ

-   **URL**: `http://prometheus.localhost` (через Traefik).
-   **Прямой доступ**: `http://localhost:9090`.