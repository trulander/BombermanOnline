# Loki
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/loki/index.md)

## Назначение

**Loki** — это система агрегации логов, разработанная Grafana. Она эффективно хранит логи и индексирует только их метаданные (лейблы), что обеспечивает высокую производительность.

## Конфигурация из docker-compose.yml

```yaml
services:
  loki:
    image: grafana/loki:3.5.0
    volumes:
      - ./loki/loki-config.yml:/etc/loki/local-config.yaml
      - loki_data:/loki
    ports:
      - "3100:3100"
    command: -config.file=/etc/loki/local-config.yaml -target=all -log.level=info
    networks:
      default:
        aliases:
          - loki.internal
```

-   **`image`**: `grafana/loki:3.5.0`.
-   **`volumes`**: Монтируется конфигурационный файл `loki-config.yml` и том `loki_data` для хранения логов.
-   **`command`**: Запускает Loki с указанным файлом конфигурации.
-   **`ports`**: `3100:3100` - порт для API.
-   **`networks.default.aliases`**: Создает сетевой псевдоним `loki.internal`, который используется сервисом `fluent-bit` для надежной отправки логов внутри Docker-сети.

## Взаимодействие с другими сервисами

-   **Fluent Bit**: Принимает потоки логов от `fluent-bit`.
-   **Grafana**: Служит источником данных для Grafana, которая запрашивает и отображает логи.

## Доступ

-   Сервис является внутренним и не имеет прямого доступа через Traefik.
