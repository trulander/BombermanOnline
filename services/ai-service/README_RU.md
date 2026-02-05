# AI Сервис (AI Service)
[![English](https://img.shields.io/badge/lang-English-blue)](README.md)

AI Сервис — компонент платформы Bomberman Online, отвечающий за управление AI-юнитами (врагами и игроками-ботами) в игровых сессиях, а также за обучение моделей искусственного интеллекта.

## Назначение сервиса

Сервис симулирует поведение AI-управляемых сущностей в игровом мире. Он получает состояние игры от `game-service`, принимает решения на основе загруженных моделей и отправляет команды управления обратно через grpc.

## Используемые технологии

*   **Python 3.12**
*   **FastAPI** & **Uvicorn**
*   **gRPC** для межсервисного синхронного взаимодействия
*   **NATS (`nats-py`)** для асинхронного взаимодействия, получение списка game-service инстансов из game-allocator-service
*   **Redis (`redis-py`)** для кэширования
*   **Gymnasium**, **Stable-Baselines3**, **TensorBoard** для обучения моделей
*   **Pydantic** для валидации и конфигурации
*   **Numpy** для работы с данными
*   **`uv`** для управления зависимостями

## Базовый каркас обучения и инференса

-   gRPC запускает обучение и инференс, HTTP эндпоинт для обучения не используется.
-   Gymnasium окружение `BombermanEnv` проксирует `reset/step` в gRPC клиент к `game-service` в режиме тренировки.
-   Stable-Baselines3 сохраняет модели в `MODELS_PATH`, TensorBoard логи пишутся в `LOGS_PATH` и читаются из `tensorboard` в `infra/docker-compose.yml`.

## gRPC тренировка

-   `Reset` создает новую тренировочную сессию в `game-service` и возвращает `session_id` и наблюдение.
-   `Step` принимает `action` и `delta_seconds` (по умолчанию 0.33 сек) и возвращает новое наблюдение, `reward`, `terminated`, `truncated`.
-   Наблюдение — вектор из окна карты `15x15` (225 значений) + 6 скаляров: `x_norm`, `y_norm`, `lives_norm`, `enemy_norm`, `map_width_norm`, `map_height_norm`.
-   Действия: `0` — no-op, `1` — up, `2` — down, `3` — left, `4` — right, `5` — place_weapon_1.

## Postman

Файлы для импорта в Postman находятся в `services/ai-service/postman`:

- `ai-service-rest.postman_collection.json` — REST эндпоинты
- `ai-service.postman_environment.json` — окружение


## Документация

Вся подробная документация по сервису разделена на следующие разделы:

*   **[Структура проекта](docs/ru/project_structure.md)**: Описание файлов и директорий.
*   **[Зависимости и технологии](docs/ru/packages.md)**: Подробный обзор используемых библиотек.
*   **[Развертывание и запуск](docs/ru/deployment.md)**: Инструкции по локальному запуску и использованию Docker.
*   **[Взаимодействие и Use Cases](docs/ru/interaction.md)**: Описание NATS API, диаграммы и сценарии использования.
*   **[Обучение моделей AI](docs/ru/ai_training.md)**: Детали процесса обучения с подкреплением.
*   **[Конфигурация](docs/ru/configuration.md)**: Полный список переменных окружения.
*   **[Поток обучения и инференса](docs/ru/examples/ai_service_flow.md)**: Диаграмма взаимодействий.
*   **[Поток тренировки](docs/ru/examples/ai_training_flow.md)**: Диаграмма тренировки через gRPC.

## Управление секретами

Секреты хранятся в Infisical. Файл `.env-example` содержит все доступные переменные и может быть импортирован в Infisical как базовая конфигурация. Docker entrypoint входит в Infisical и запускает сервис с подставленными переменными окружения.

## Тестирование

Из директории `services/ai-service`:

```bash
uv pip install .
uv run pytest
```