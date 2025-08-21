# Node Exporter и cAdvisor
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/node-exporter-cadvisor/index.md)

## Назначение в проекте

**Node Exporter** и **cAdvisor** — это агенты для сбора метрик, которые поставляют данные в Prometheus.

-   **`node-exporter`**: Собирает метрики **хост-системы**, на которой запущен Docker (CPU, RAM, диск, сеть).
-   **`cadvisor` (Container Advisor)**: Собирает метрики производительности и использования ресурсов по **каждому запущенному Docker-контейнеру**.

Эти два компонента обеспечивают полное покрытие метриками как на уровне "железа", так и на уровне отдельных приложений.

## Конфигурация

Оба сервиса определены в `infra/docker-compose.yml`.

### Node Exporter
```yaml
services:
  node-exporter:
    image: prom/node-exporter:v1.7.0
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    ports:
      - "9100:9100"
```
-   Пробрасывает файловые системы хоста для сбора метрик. Отдает метрики на порту `9100`.

### cAdvisor
```yaml
services:
  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.2
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      # ... и другие системные директории
    ports:
      - "8081:8080"
```
-   Также монтирует системные директории и сокет Docker. Отдает метрики на порту `8080`.

## Доступ

-   Оба сервиса являются внутренними. Prometheus напрямую собирает с них метрики по портам `9100` и `8080` соответственно.
-   `cAdvisor` имеет собственный веб-интерфейс для отладки, доступный на `http://localhost:8081`.
