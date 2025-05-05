# Архитектура проекта Bomberman Online

## Диаграмма компонентов

```mermaid
C4Component
    title Архитектура Bomberman Online

    Container_Boundary(api, "FastAPI Application") {
        Component(routes, "Routes", "FastAPI Router", "Обработка HTTP запросов")
        Component(services, "Services", "Business Logic", "Игровая логика и управление состоянием")
        Component(models, "Models", "Domain Models", "Игровые сущности")
        Component(repositories, "Repositories", "Data Access", "Доступ к данным")
        Component(config, "Config", "Settings", "Конфигурация приложения")
    }

    Container(redis, "Redis", "Cache", "Кэширование игровых данных")
    Container(postgres, "PostgreSQL", "Database", "Хранение игровых данных")
    Container(socketio, "Socket.IO", "WebSocket", "Реалтайм коммуникация")

    Rel(routes, services, "Использует")
    Rel(services, models, "Управляет")
    Rel(services, repositories, "Использует")
    Rel(services, socketio, "Отправляет события")
    Rel(repositories, redis, "Кэширует")
    Rel(repositories, postgres, "Сохраняет")
    Rel(services, config, "Читает настройки")
```

## Структура проекта

```
server2/
├── app/
│   ├── __init__.py
│   ├── main.py           # Основной файл приложения
│   ├── config.py         # Конфигурация приложения
│   ├── routes/           # Маршруты API
│   │   ├── __init__.py
│   │   └── game_routes.py
│   ├── services/         # Бизнес-логика
│   │   ├── __init__.py
│   │   └── game_service.py
│   ├── models/          # Модели данных
│   │   └── __init__.py
│   └── repositories/    # Репозитории для работы с данными
│       ├── __init__.py
│       ├── redis_repository.py
│       └── postgres_repository.py
├── game/               # Игровая логика
│   ├── __init__.py
│   ├── game.py
│   ├── player.py
│   ├── enemy.py
│   ├── bomb.py
│   ├── map.py
│   └── power_up.py
├── .env-example        # Пример файла с переменными окружения
└── README.md          # Документация проекта
```