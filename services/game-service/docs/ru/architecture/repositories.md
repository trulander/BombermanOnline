[![English](https://img.shields.io/badge/lang-English-blue)](../../en/architecture/repositories.md)

# Слой доступа к данным (Репозитории)

Слой репозиториев в Game Service отвечает за инкапсуляцию логики доступа к различным источникам данных: PostgreSQL, Redis и NATS. Это позволяет отделить бизнес-логику от деталей реализации хранения и получения данных.

## 1. `BaseRepository` (`app/repositories/__init__.py`)

-   **Описание**: Абстрактный базовый класс (Generic ABC) для всех репозиториев. Определяет стандартный CRUD-подобный интерфейс, который могут реализовывать конкретные репозитории.
-   **Абстрактные методы**:
    -   `get(id: str) -> T | None`: Получить объект по идентификатору.
    -   `create(data: T) -> T`: Создать новый объект.
    -   `update(id: str, data: T) -> T | None`: Обновить существующий объект.
    -   `delete(id: str) -> bool`: Удалить объект.
-   **Назначение**: Хотя он определен, в текущей кодовой базе `MapRepository` не наследуется от него напрямую и реализует свой собственный набор методов. Другие репозитории (`PostgresRepository`, `RedisRepository`, `NatsRepository`) также не следуют этому интерфейсу, так как они предоставляют более специфичные методы для своих источников данных.

## 2. `PostgresRepository` (`app/repositories/postgres_repository.py`)

-   **Описание**: Обеспечивает подключение и взаимодействие с базой данных PostgreSQL с использованием SQLAlchemy в асинхронном режиме (`asyncpg` драйвер).
-   **Ключевые компоненты и методы**:
    -   `engine: sa_asyncio.AsyncEngine`: Асинхронный движок SQLAlchemy.
    -   `async_session: sa_asyncio.async_sessionmaker`: Фабрика для создания асинхронных сессий.
    -   `connect()`: Устанавливает асинхронное подключение к PostgreSQL, создает движок и фабрику сессий. Выполняет тестовый запрос `SELECT 1` для проверки соединения.
    -   `disconnect()`: Закрывает соединение с базой данных.
    -   `_ensure_connected()`: Проверяет состояние подключения и переподключается при необходимости перед каждой операцией.
    -   `get_session()`: Асинхронный контекстный менеджер, предоставляющий сессию SQLAlchemy. Автоматически выполняет `commit` при успешном завершении блока `try` или `rollback` при исключении. Сессия закрывается в блоке `finally`.
-   **Использование**: Используется `MapRepository` для выполнения операций CRUD с ORM-моделями карт.

## 3. `RedisRepository` (`app/repositories/redis_repository.py`)

-   **Описание**: Предоставляет методы для взаимодействия с сервером Redis (асинхронно).
-   **Ключевые компоненты и методы**:
    -   `_redis: redis.Redis`: Экземпляр асинхронного клиента Redis.
    -   `get_redis()`: Возвращает активное подключение к Redis, создавая его при первом вызове или если оно было закрыто. Выполняет `ping` для проверки соединения.
    -   `disconnect()`: Закрывает подключение к Redis.
    -   `set(key: str, value: Any, expire: int = 0) -> bool`: Сериализует `value` в JSON и сохраняет в Redis по ключу `key` с опциональным временем жизни `expire` (в секундах).
    -   `get(key: str) -> Any`: Получает значение по ключу `key` из Redis и десериализует его из JSON. Возвращает `None`, если ключ не найден.
    -   `delete(key: str) -> bool`: Удаляет ключ из Redis.
-   **Использование**: Используется `MapRepository` для кеширования данных о шаблонах, группах и цепочках карт.

## 4. `NatsRepository` (`app/repositories/nats_repository.py`)

-   **Описание**: Инкапсулирует низкоуровневое взаимодействие с сервером NATS для публикации и подписки на сообщения.
-   **Ключевые компоненты и методы**:
    -   `_nc: NATS | None`: Экземпляр клиента NATS.
    -   `get_nc()`: Возвращает активное подключение к NATS, устанавливая его при необходимости.
    -   `disconnect()`: Корректно закрывает соединение с NATS (выполняет `drain`).
    -   `_publish_data(subject: str, payload: dict) -> bool`: Внутренний метод для сериализации `payload` в JSON (с поддержкой NumPy типов) и публикации данных с логикой повторных попыток.
    -   `_send_event_with_reconnect(subject: str, payload_bytes: bytes, max_retries: int = 3, retry_delay: float = 1.0) -> bool`: Отправляет событие с автоматическим переподключением и повторными попытками в случае сбоев.
    -   `publish_event(subject_base: str, payload: dict, game_id: Optional[str] = None, specific_suffix: Optional[str] = None) -> bool`: Публикует событие, конструируя тему (subject) из базовой части, ID игры и суффикса.
    -   `publish_simple(subject: str, payload: any) -> bool`: Упрощенная публикация данных.
    -   `subscribe(subject: str, callback)`: Подписывается на указанную тему NATS, вызывая `callback` при получении сообщения.
-   **Использование**: Используется `EventService` для всей NATS-коммуникации.

## 5. `MapRepository` (`app/repositories/map_repository.py`)

-   **Описание**: Специализированный репозиторий для управления данными, связанными с картами (шаблоны, группы, цепочки). Он комбинирует использование PostgreSQL для персистентного хранения и Redis для кеширования.
-   **Зависимости**: `PostgresRepository`, `RedisRepository`.
-   **Ключевые методы (для MapTemplate, аналогичные для MapGroup и MapChain)**:
    -   `create_map_template(template_data: MapTemplateCreate, created_by: str) -> MapTemplate`:
        1.  Создает новую запись `MapTemplateORM` в PostgreSQL.
        2.  Конвертирует ORM-объект в Pydantic модель `MapTemplate`.
        3.  Кеширует Pydantic модель (сериализованную в dict, с датами в ISO формате) в Redis.
    -   `get_map_template(map_id: str) -> Optional[MapTemplate]`:
        1.  Пытается получить данные из кеша Redis.
        2.  Если в кеше нет, запрашивает из PostgreSQL (`is_active == True`).
        3.  Если найдено в БД, конвертирует в Pydantic модель и кеширует в Redis.
    -   `update_map_template(map_id: str, template_data: MapTemplateUpdate) -> Optional[MapTemplate]`:
        1.  Обновляет запись в PostgreSQL.
        2.  Получает обновленную запись из БД.
        3.  Конвертирует в Pydantic модель.
        4.  Обновляет кеш в Redis.
    -   `delete_map_template(map_id: str) -> bool` (мягкое удаление):
        1.  Устанавливает `is_active = False` в PostgreSQL.
        2.  Удаляет запись из кеша Redis.
    -   `list_map_templates(filter_params: MapTemplateFilter) -> List[MapTemplate]`:
        1.  Выполняет запрос к PostgreSQL с учетом фильтров (имя, сложность, игроки, создатель) и пагинации (`limit`, `offset`).
        2.  Конвертирует результаты в список Pydantic моделей `MapTemplate`.
        3.  (Кеширование для списков здесь не реализовано).
    -   `get_maps_by_difficulty(min_difficulty: int, max_difficulty: int) -> List[MapTemplate]`: Получает карты по диапазону сложности.
-   **Логика кеширования**: Данные кешируются в Redis с TTL (по умолчанию 1 час). Ключи кеша имеют префиксы (например, `map_template:{id}`). Даты сохраняются в кеше в формате ISO и восстанавливаются при чтении.