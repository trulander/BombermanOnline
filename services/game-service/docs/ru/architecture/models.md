# Модели Данных

В этом разделе описываются модели данных, используемые в игровом сервисе. Сюда входят Pydantic модели для валидации данных API и настроек создания игры, а также SQLAlchemy модели для определения структуры таблиц в базе данных. 

## 1. SQLAlchemy ORM Модели

Эти модели определяют структуру таблиц в базе данных PostgreSQL, используемой игровым сервисом. Они разработаны с использованием SQLAlchemy ORM.

### 1.1. `MapTemplateORM`

Представляет таблицу `map_templates`, в которой хранятся шаблоны игровых карт.

- **Поля:**
    - `id` (String, Primary Key): Уникальный идентификатор шаблона карты.
    - `name` (String): Название шаблона карты.
    - `description` (Text, Optional): Описание шаблона карты.
    - `width` (Integer): Ширина карты в клетках.
    - `height` (Integer): Высота карты в клетках.
    - `grid_data` (JSON): 2D-массив (список списков чисел), представляющий сетку карты и расположение элементов на ней.
    - `difficulty` (Integer): Уровень сложности карты (1-10).
    - `max_players` (Integer): Максимальное количество игроков (1-8).
    - `min_players` (Integer): Минимальное количество игроков (>=1).
    - `estimated_play_time` (Integer): Примерное время игры на карте в секундах.
    - `tags` (JSON, Optional): Список тегов для классификации карты.
    - `created_by` (String): Идентификатор пользователя, создавшего шаблон.
    - `created_at` (DateTime): Дата и время создания.
    - `updated_at` (DateTime): Дата и время последнего обновления.
    - `is_active` (Boolean): Флаг активности шаблона.

### 1.2. `MapGroupORM`

Представляет таблицу `map_groups`, которая объединяет несколько шаблонов карт в группу.

- **Поля:**
    - `id` (String, Primary Key): Уникальный идентификатор группы карт.
    - `name` (String): Название группы карт.
    - `description` (Text, Optional): Описание группы карт.
    - `map_ids` (JSON): Список идентификаторов шаблонов карт (`MapTemplateORM.id`), входящих в группу.
    - `created_by` (String): Идентификатор пользователя, создавшего группу.
    - `created_at` (DateTime): Дата и время создания.
    - `updated_at` (DateTime): Дата и время последнего обновления.
    - `is_active` (Boolean): Флаг активности группы.

### 1.3. `MapChainORM`

Представляет таблицу `map_chains`, которая определяет последовательность карт (цепочку) для прохождения, возможно с нарастающей сложностью.

- **Поля:**
    - `id` (String, Primary Key): Уникальный идентификатор цепочки карт.
    - `name` (String): Название цепочки карт.
    - `description` (Text, Optional): Описание цепочки карт.
    - `map_ids` (JSON): Список идентификаторов шаблонов карт (`MapTemplateORM.id`), составляющих цепочку.
    - `difficulty_progression` (Float): Коэффициент прогрессии сложности для карт в цепочке.
    - `created_by` (String): Идентификатор пользователя, создавшего цепочку.
    - `created_at` (DateTime): Дата и время создания.
    - `updated_at` (DateTime): Дата и время последнего обновления.
    - `is_active` (Boolean): Флаг активности цепочки.

## 2. Pydantic Модели

Эти модели используются для валидации данных в HTTP API запросах и ответах, а также для определения структуры настроек при создании игры.

### 2.1. Модели для API Карт

Эти модели определены в `app/models/map_models.py`.

#### 2.1.1. Шаблоны Карт (`MapTemplate`)

-   **`MapTemplateBase`**: Базовая модель для шаблона карты.
    -   `name` (str): Название.
    -   `description` (Optional[str]): Описание.
    -   `width` (int): Ширина (5-50).
    -   `height` (int): Высота (5-50).
    -   `grid_data` (List[List[int]]): Данные сетки карты.
    -   `difficulty` (int): Сложность (1-10).
    -   `max_players` (int): Макс. игроков (1-8).
    -   `min_players` (int): Мин. игроков (>=1).
    -   `estimated_play_time` (int): Примерное время игры (в секундах, >=60).
    -   `tags` (List[str]): Теги.
-   **`MapTemplateCreate`**: Модель для создания нового шаблона карты (наследуется от `MapTemplateBase`).
-   **`MapTemplateUpdate`**: Модель для обновления существующего шаблона карты (все поля опциональны).
-   **`MapTemplate`**: Модель для представления шаблона карты в API ответах (включает `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Имеет конфигурацию `from_attributes = True` для работы с ORM объектами.
    -   Содержит метод `from_orm` для преобразования объекта `MapTemplateORM`.

#### 2.1.2. Группы Карт (`MapGroup`)

-   **`MapGroupBase`**: Базовая модель для группы карт.
    -   `name` (str): Название.
    -   `description` (Optional[str]): Описание.
    -   `map_ids` (List[str]): Список ID шаблонов карт (минимум 1 элемент).
-   **`MapGroupCreate`**: Модель для создания новой группы карт (наследуется от `MapGroupBase`).
-   **`MapGroupUpdate`**: Модель для обновления существующей группы карт (все поля опциональны).
-   **`MapGroup`**: Модель для представления группы карт в API ответах (включает `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Имеет конфигурацию `from_attributes = True`.
    -   Содержит метод `from_orm` для преобразования объекта `MapGroupORM`.

#### 2.1.3. Цепочки Карт (`MapChain`)

-   **`MapChainBase`**: Базовая модель для цепочки карт.
    -   `name` (str): Название.
    -   `description` (Optional[str]): Описание.
    -   `map_ids` (List[str]): Список ID шаблонов карт (минимум 1 элемент).
    -   `difficulty_progression` (float): Коэффициент прогрессии сложности (0.1-5.0).
-   **`MapChainCreate`**: Модель для создания новой цепочки карт (наследуется от `MapChainBase`).
-   **`MapChainUpdate`**: Модель для обновления существующей цепочки карт (все поля опциональны).
-   **`MapChain`**: Модель для представления цепочки карт в API ответах (включает `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Имеет конфигурацию `from_attributes = True`.
    -   Содержит метод `from_orm` для преобразования объекта `MapChainORM`.

### 2.2. Модели для API Команд

Эти модели определены в `app/models/team_models.py` и используются для управления командами через REST API.

#### 2.2.1. Команды (`Team`)

-   **`TeamBase`**: Базовая модель для команды.
    -   `name` (str): Название команды (1-50 символов).

-   **`TeamCreate`**: Модель для создания новой команды (наследуется от `TeamBase`).

-   **`TeamUpdate`**: Модель для обновления существующей команды.
    -   `name` (Optional[str]): Новое название команды (1-50 символов).

-   **`Team`**: Модель для представления команды в API ответах.
    -   `id` (str): Уникальный идентификатор команды.
    -   `name` (str): Название команды.
    -   `score` (int): Очки команды (по умолчанию 0).
    -   `player_ids` (List[str]): Список ID игроков в команде.
    -   `player_count` (int): Количество игроков в команде (по умолчанию 0).
    -   Имеет конфигурацию `from_attributes = True` для работы с entity объектами.

#### 2.2.2. Действия с игроками в командах

-   **`PlayerTeamAction`**: Модель для добавления/удаления игрока из команды.
    -   `player_id` (str): ID игрока.

-   **`TeamDistributionRequest`**: Модель для автоматического распределения игроков по командам.
    -   `redistribute_existing` (bool): Перераспределить существующих игроков (по умолчанию False).

### 2.3. Модели Фильтров для API Карт

Эти модели определены в `app/models/map_models.py` и используются для фильтрации списков при запросах к API.

-   **`MapTemplateFilter`**: Фильтры для поиска шаблонов карт.
    -   `name` (Optional[str])
    -   `difficulty_min` (Optional[int], 1-10)
    -   `difficulty_max` (Optional[int], 1-10)
    -   `max_players_min` (Optional[int], 1-8)
    -   `max_players_max` (Optional[int], 1-8)
    -   `tags` (Optional[List[str]])
    -   `created_by` (Optional[str])
    -   `is_active` (Optional[bool], default: True)
    -   `limit` (int, default: 20, 1-100)
    -   `offset` (int, default: 0, >=0)
-   **`MapGroupFilter`**: Фильтры для поиска групп карт.
    -   `name` (Optional[str])
    -   `created_by` (Optional[str])
    -   `is_active` (Optional[bool], default: True)
    -   `limit` (int, default: 20, 1-100)
    -   `offset` (int, default: 0, >=0)
-   **`MapChainFilter`**: Фильтры для поиска цепочек карт.
    -   `name` (Optional[str])
    -   `created_by` (Optional[str])
    -   `is_active` (Optional[bool], default: True)
    -   `limit` (int, default: 20, 1-100)
    -   `offset` (int, default: 0, >=0)

### 2.4. Модели для Создания Игры

Эта модель определена в `app/models/game_create_models.py`.

-   **`GameCreateSettings`**: Определяет настройки для создания новой игровой сессии.
    -   `game_id` (Optional[str]): ID игры (может быть присвоен позже).
    -   `game_mode` (`GameModeType`): Режим игры (например, `CAMPAIGN`).
    -   `max_players` (int): Максимальное количество игроков.
    -   `team_count` (int): Количество команд.
    -   `player_start_lives` (int): Начальное количество жизней у игрока.
    -   `enable_enemies` (bool): Включены ли враги.
    -   `map_chain_id` (Optional[str]): ID цепочки карт.
    -   `map_template_id` (Optional[str]): ID шаблона карты.
    -   `respawn_enabled` (bool): Включен ли респаун.
    -   `friendly_fire` (bool): Включен ли "огонь по своим".
    -   `time_limit` (Optional[int]): Лимит времени на игру в секундах.
    -   `score_limit` (Optional[int]): Лимит очков для победы.
    -   `rounds_count` (Optional[int]): Количество раундов. 