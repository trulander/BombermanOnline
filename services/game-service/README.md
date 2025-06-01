# Bomberman Game Service

Микросервис игровой логики для онлайн игры Bomberman с поддержкой различных игровых режимов и кастомных карт.

## Особенности

### Игровые режимы
- **Single Player** - прохождение одним игроком с увеличивающейся сложностью
- **Deathmatch** - все против всех до последнего выжившего
- **Cooperative** - совместное прохождение уровней
- **Team Capture Flag** - командная игра с захватом флагов
- **Custom** - настраиваемая игра с кастомными параметрами

### Система карт
- **Случайная генерация** карт с различными размерами и сложностью
- **Шаблоны карт** из PostgreSQL базы данных с кешированием в Redis
- **Группы карт** для различных режимов игры
- **Цепочки карт** для последовательного прохождения
- **Редактор карт** (в разработке)

### Архитектура
- **SOLID принципы** и чистая архитектура
- **MapService** для управления генерацией и наполнением карт
- **GameSettings** для гибких настроек игры
- **Разделение ответственности** между сервисами

## Технологии

- **Python 3.12+** с современным синтаксисом и типизацией
- **FastAPI** для HTTP API
- **PostgreSQL** для хранения карт и их характеристик
- **Redis** для кеширования карт
- **NATS** для real-time коммуникации
- **AsyncPG** для асинхронной работы с PostgreSQL
- **Docker** для контейнеризации

## Установка

### Требования
- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- NATS Server

### Установка зависимостей

```bash
# Установка UV (рекомендуемый менеджер пакетов)
pip install uv

# Установка зависимостей проекта
uv pip install -e .
```

### Настройка окружения

Скопируйте `.env-example` в `.env` и настройте переменные:

```bash
cp .env-example .env
```

Основные настройки:

```env
# PostgreSQL settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=bomberman_maps
DB_USER=postgres
DB_PASSWORD=password

# Redis settings
REDIS_HOST=localhost
REDIS_PORT=6379

# NATS settings
NATS_URL=nats://localhost:4222

# Game settings
GAME_UPDATE_FPS=30.0
MAP_WIDTH=15
MAP_HEIGHT=13
```

### Инициализация базы данных

Выполните SQL скрипт для создания таблиц карт:

```bash
psql -h localhost -U postgres -d bomberman_maps -f alembic/versions/001_create_map_tables.sql
```

## Запуск

### Локальный запуск

```bash
# Запуск сервиса
python -m app.main

# Или через uvicorn
uvicorn app.main:app --host 0.0.0.0 --port 5002 --reload
```

### Docker

```bash
# Сборка образа
docker build -t bomberman-game-service .

# Запуск контейнера
docker run -p 5002:5002 --env-file .env bomberman-game-service
```

### Docker Compose

См. основной `docker-compose.yml` в корне проекта.

## Структура проекта

```
app/
├── entities/           # Игровые сущности
│   ├── cell_type.py   # Типы клеток карты
│   ├── game_mode.py   # Игровые режимы
│   ├── game_settings.py # Настройки игры
│   ├── map.py         # Упрощенная карта
│   ├── player.py      # Игрок
│   ├── enemy.py       # Враги
│   ├── bomb.py        # Бомбы
│   └── power_up.py    # Усиления
├── services/          # Бизнес-логика
│   ├── game_service.py      # Основная игровая логика
│   ├── map_service.py       # Управление картами
│   └── nats_service.py      # NATS коммуникация
├── repositories/      # Доступ к данным
│   └── map_repository.py    # Репозиторий карт
├── coordinators/      # Координаторы
│   └── game_coordinator.py # Координатор игр
├── models/           # Модели данных
│   └── map_models.py # Модели карт
└── config.py         # Конфигурация
```

## API Endpoints

### Health Check
```
GET /health
```

### Metrics
```
GET /metrics
```

## Игровые события (NATS)

### Подписки сервиса
- `game.create` - создание новой игры
- `game.join` - присоединение к игре
- `game.input` - ввод игрока
- `game.place_bomb` - размещение бомбы
- `game.get_state` - получение состояния игры
- `game.disconnect` - отключение игрока

### Публикации сервиса
- `game.update.{game_id}` - обновления состояния игры
- `game.over.{game_id}` - окончание игры
- `game.player_disconnected.{game_id}` - отключение игрока

## Создание карт

### Структура карты в JSON

```json
{
  "width": 15,
  "height": 15,
  "grid_data": [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,3,0,2,0,2,0,2,0,2,0,2,0,3,1],
    ...
  ]
}
```

### Типы клеток
- `0` - пустая клетка
- `1` - твердая стена
- `2` - разрушаемый блок
- `3` - точка спавна игрока
- `4` - точка спавна врага
- `5` - точка спавна усилений

## Мониторинг

Сервис предоставляет метрики Prometheus:
- Количество активных игр
- Количество подключенных игроков
- Время обработки запросов
- Статистика игровых событий

## Разработка

### Добавление нового игрового режима

1. Добавьте новый тип в `GameModeType` (`entities/game_mode.py`)
2. Обновите логику в `GameService` для обработки режима
3. Добавьте специфичную логику в `update()` методе

### Создание нового типа врага

1. Добавьте тип в `EnemyType` (`entities/enemy.py`)
2. Обновите константы `ENEMY_LIVES`
3. Реализуйте специфичное поведение в `update_enemy()`

### Добавление нового типа усиления

1. Добавьте тип в `PowerUpType` (`entities/power_up.py`)
2. Реализуйте логику в `apply_to_player()`

## Логирование

Сервис использует структурированное JSON логирование с поддержкой:
- Трассировки вызовов
- Контекстной информации
- Метрик производительности

## Тестирование

```bash
# Запуск тестов
python -m pytest

# Запуск с coverage
python -m pytest --cov=app
```

## Миграции

Для обновления схемы базы данных используйте Alembic:

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head
```