# Grafana
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/grafana/index.md)

## Назначение в проекте

**Grafana** — это платформа для визуализации, мониторинга и анализа данных. Она используется как единый интерфейс для просмотра метрик из Prometheus и логов из Loki.

## Конфигурация из docker-compose.yml

```yaml
services:
  grafana:
    image: grafana/grafana:12.0.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
      - ./grafana/dashboards:/var/lib/grafana/dashboards
    environment:
      - GF_SECURITY_ADMIN_USER=${GRAFANA_ADMIN_USER:-admin}
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_ADMIN_PASSWORD:-admin}
      - GF_SERVER_ROOT_URL=http://localhost:3001
      - GF_USERS_ALLOW_SIGN_UP=false
      - GF_SERVER_HTTP_PORT=3001
      - GF_DASHBOARDS_MIN_REFRESH_INTERVAL=5s
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
    ports:
      - "3001:3001"
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.grafana.rule=Host(`grafana.localhost`)"
      - "traefik.http.services.grafana.loadbalancer.server.port=3001"
```

-   **`image`**: `grafana/grafana:12.0.0`.
-   **`volumes`**: Монтируются директории для хранения данных Grafana, а также для автоматической конфигурации (`provisioning`) источников данных и дашбордов.
-   **`environment`**: Задается множество переменных для конфигурации Grafana, включая:
    -   `GF_SECURITY_ADMIN_USER`/`PASSWORD`: Учетные данные администратора.
    -   `GF_USERS_ALLOW_SIGN_UP=false`: Запрещает регистрацию новых пользователей.
    -   `GF_AUTH_ANONYMOUS_ENABLED=true`: Разрешает анонимный доступ с ролью `Viewer`.
-   **`labels`**: Настраивают Traefik для доступа к Grafana по адресу `grafana.localhost`.

## Взаимодействие с другими сервисами

-   **Prometheus**: Grafana использует Prometheus как основной источник данных для получения метрик.
-   **Loki**: Использует Loki как источник данных для отображения и запроса логов.
-   **Provisioning**: При старте автоматически настраивает подключения к Prometheus и Loki на основе файлов в `./grafana/provisioning/datasources` и загружает все дашборды из `./grafana/dashboards`.

## Доступ

-   **URL**: `http://grafana.localhost` (через Traefik).
-   **Прямой доступ**: `http://localhost:3001`.
-   **Логин/Пароль**: `admin`/`admin`.
