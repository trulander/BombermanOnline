# Prometheus
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/prometheus/index.md)

## Назначение в проекте

**Prometheus** — это система **мониторинга и сбора метрик**. Она является центральным компонентом для сбора данных о производительности и состоянии всех сервисов в проекте.

Prometheus периодически опрашивает (scrapes) HTTP-эндпоинты `/metrics`, предоставляемые различными сервисами и экспортерами, и сохраняет полученные данные в своей базе временных рядов. Эти данные затем используются в **Grafana** для построения графиков и дашбордов.

## Конфигурация

Основной конфигурационный файл находится в `infra/prometheus/prometheus.yml`.

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "prometheus"
    static_configs:
      - targets: ["localhost:9090"]

  # ... другие job ...
```

### Цели для сбора метрик (Scrape Targets)

Согласно `prometheus.yml`, настроен сбор метрик со следующих сервисов и экспортеров:

-   `prometheus`: сам себя (localhost:9090)
-   `webapi-service`: `webapi-service:5001` (интервал 5с)
-   `game-service`: `game-service:5002` (интервал 5с)
-   `node-exporter`: `node-exporter:9100` (метрики хост-машины)
-   `cadvisor`: `cadvisor:8080` (метрики Docker-контейнеров)
-   `redis-exporter`: `redis-exporter:9121` (метрики Redis)
-   `nats-exporter`: `prometheus-nats-exporter:7777` (метрики NATS)
-   `loki`: `loki:3100`
-   `fluent-bit`: `fluent-bit:2020`
-   `grafana`: `grafana:3001`

## Доступ через Traefik

-   **URL**: `http://prometheus.localhost`
-   Этот эндпоинт настроен в `docker-compose.yml` через лейблы у сервиса `prometheus` и позволяет получить доступ к веб-интерфейсу Prometheus для выполнения запросов PromQL и проверки состояния целей.
