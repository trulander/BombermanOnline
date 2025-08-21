# TensorBoard
[![English](https://img.shields.io/badge/lang-English-blue.svg)](../../../en/infra/tensorboard/index.md)

## Назначение в проекте

**TensorBoard** — это инструмент визуализации, входящий в экосистему TensorFlow. В данном проекте он используется для **визуализации процесса обучения AI-моделей**.

`ai-service` во время тренировки моделей сохраняет логи обучения (например, значения функции потерь, точность, градиенты) в специальном формате. TensorBoard читает эти логи и представляет их в виде интерактивных графиков и дашбордов.

Это позволяет:
-   Отслеживать прогресс обучения в реальном времени.
-   Анализировать и сравнивать разные запуски моделей.
-   Отлаживать архитектуру нейронной сети и гиперпараметры.

## Конфигурация

Сервис `tensorboard` определен в `infra/docker-compose.yml`:

```yaml
services:
  tensorboard:
    image: tensorflow/tensorboard:latest
    volumes:
      - ../infra/ai_logs:/tf/logs
    ports:
      - "6006:6006"
    command: tensorboard --logdir=/tf/logs --host 0.0.0.0 --port 6006
```

-   **`image`**: `tensorflow/tensorboard:latest` - официальный образ.
-   **`volumes`**: Директория `infra/ai_logs` с хост-машины, куда `ai-service` сохраняет логи, монтируется внутрь контейнера в `/tf/logs`.
-   **`ports`**: `6006:6006` - стандартный порт для доступа к веб-интерфейсу TensorBoard.
-   **`command`**: Запускает TensorBoard и указывает ему читать логи из директории `/tf/logs`.

## Доступ

-   **Веб-интерфейс TensorBoard**: `http://localhost:6006`
-   Сервис не маршрутизируется через Traefik.
