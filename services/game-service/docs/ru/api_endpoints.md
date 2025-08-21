[![English](https://img.shields.io/badge/lang-English-blue)](../en/api_endpoints.md)

# API-эндпоинты игрового сервиса (Game Service API Endpoints)

Этот документ описывает HTTP API-эндпоинты, предоставляемые сервисом `Game Service`. Все эндпоинты имеют префикс `/games/api/v1`.

## Эндпоинты игр (`/games`)

*   `GET /games/`
    *   **Описание**: Получить список игр с фильтрацией.
    *   **Параметры запроса (Query Parameters)**:
        *   `status` (Optional[GameStatus]): Фильтр по статусу игры (`PENDING`, `ACTIVE`, `PAUSED`, `FINISHED`).
        *   `game_mode` (Optional[GameModeType]): Фильтр по игровому режиму (`CAMPAIGN`, `FREE_FOR_ALL`, `CAPTURE_THE_FLAG`).
        *   `has_free_slots` (Optional[bool]): Фильтр по наличию свободных слотов.
        *   `min_players` (Optional[int]): Минимальное количество игроков.
        *   `max_players` (Optional[int]): Максимальное количество игроков.
        *   `limit` (int): Количество записей на страницу (по умолчанию 20).
        *   `offset` (int): Смещение для пагинации (по умолчанию 0).
    *   **Ответ**: `List[GameListItem]`
*   `GET /games/{game_id}`
    *   **Описание**: Получить подробную информацию об игре по ID.
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
    *   **Ответ**: `GameInfo`
*   `PUT /games/{game_id}/settings`
    *   **Описание**: Обновить настройки игры (только для игр в статусе `PENDING`).
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
    *   **Тело запроса (Request Body)**: `GameSettingsUpdate` (JSON).
    *   **Ответ**: `StandardResponse`
*   `PUT /games/{game_id}/status`
    *   **Описание**: Изменить статус игры (`start`/`pause`/`resume`).
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
    *   **Тело запроса (Request Body)**: `GameStatusUpdate` (JSON).
    *   **Ответ**: `StandardResponse`
*   `POST /games/{game_id}/players`
    *   **Описание**: Добавить игрока в игру.
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
    *   **Тело запроса (Request Body)**: `PlayerAction` (JSON).
    *   **Ответ**: `StandardResponse`
*   `DELETE /games/{game_id}/players/{player_id}`
    *   **Описание**: Удалить игрока из игры.
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
        *   `player_id` (str): Уникальный идентификатор игрока.
    *   **Ответ**: `StandardResponse`
*   `DELETE /games/{game_id}`
    *   **Описание**: Удалить игру (мягкое удаление).
    *   **Параметры пути (Path Parameters)**:
        *   `game_id` (str): Уникальный идентификатор игры.
    *   **Ответ**: `StandardResponse`

## Эндпоинты сущностей (`/entities`)

*   `GET /entities/info`
    *   **Описание**: Получить информацию о доступных игровых сущностях и их типах (CellType, GameModeType, GameStatus, EnemyType, PowerUpType, Player units, Weapon types) с их размерами.
    *   **Ответ**: `Dict[str, Any]`

## Эндпоинты карт (`/maps`)

*   `POST /maps/templates`
    *   **Описание**: Создать новый шаблон карты.
    *   **Тело запроса**: `MapTemplateCreate` (JSON).
    *   **Ответ**: `MapTemplate` (статус 201).
*   `GET /maps/templates`
    *   **Описание**: Получить список шаблонов карт с фильтрацией.
    *   **Параметры запроса**: `name`, `difficulty_min`, `difficulty_max`, `max_players_min`, `max_players_max`, `created_by`, `limit`, `offset`.
    *   **Ответ**: `List[MapTemplate]`.
*   `GET /maps/templates/{template_id}`
    *   **Описание**: Получить шаблон карты по ID.
    *   **Параметры пути**: `template_id`.
    *   **Ответ**: `MapTemplate`.
*   `PUT /maps/templates/{template_id}`
    *   **Описание**: Обновить шаблон карты.
    *   **Параметры пути**: `template_id`.
    *   **Тело запроса**: `MapTemplateUpdate`.
    *   **Ответ**: `MapTemplate`.
*   `DELETE /maps/templates/{template_id}`
    *   **Описание**: Удалить шаблон карты (мягкое удаление).
    *   **Параметры пути**: `template_id`.
    *   **Ответ**: Статус 204.
*   `POST /maps/groups`
    *   **Описание**: Создать новую группу карт.
    *   **Тело запроса**: `MapGroupCreate`.
    *   **Ответ**: `MapGroup` (статус 201).
*   `GET /maps/groups`
    *   **Описание**: Получить список групп карт.
    *   **Параметры запроса**: `name`, `created_by`, `limit`, `offset`.
    *   **Ответ**: `List[MapGroup]`.
*   `GET /maps/groups/{group_id}`
    *   **Описание**: Получить группу карт по ID.
    *   **Параметры пути**: `group_id`.
    *   **Ответ**: `MapGroup`.
*   `PUT /maps/groups/{group_id}`
    *   **Описание**: Обновить группу карт.
    *   **Параметры пути**: `group_id`.
    *   **Тело запроса**: `MapGroupUpdate`.
    *   **Ответ**: `MapGroup`.
*   `DELETE /maps/groups/{group_id}`
    *   **Описание**: Удалить группу карт (мягкое удаление).
    *   **Параметры пути**: `group_id`.
    *   **Ответ**: Статус 204.
*   `POST /maps/chains`
    *   **Описание**: Создать новую цепочку карт.
    *   **Тело запроса**: `MapChainCreate`.
    *   **Ответ**: `MapChain` (статус 201).
*   `GET /maps/chains`
    *   **Описание**: Получить список цепочек карт.
    *   **Параметры запроса**: `name`, `created_by`, `limit`, `offset`.
    *   **Ответ**: `List[MapChain]`.
*   `GET /maps/chains/{chain_id}`
    *   **Описание**: Получить цепочку карт по ID.
    *   **Параметры пути**: `chain_id`.
    *   **Ответ**: `MapChain`.
*   `PUT /maps/chains/{chain_id}`
    *   **Описание**: Обновить цепочку карт.
    *   **Параметры пути**: `chain_id`.
    *   **Тело запроса**: `MapChainUpdate`.
    *   **Ответ**: `MapChain`.
*   `DELETE /maps/chains/{chain_id}`
    *   **Описание**: Удалить цепочку карт (мягкое удаление).
    *   **Параметры пути**: `chain_id`.
    *   **Ответ**: Статус 204.

## Эндпоинты команд (`/teams`)

*   `GET /teams/{game_id}`
    *   **Описание**: Получить список команд для игры.
    *   **Параметры пути**: `game_id`.
    *   **Ответ**: `List[Team]`.
*   `POST /teams/{game_id}`
    *   **Описание**: Создать новую команду в игре.
    *   **Параметры пути**: `game_id`.
    *   **Тело запроса**: `TeamCreate`.
    *   **Ответ**: `Team` (статус 201).
*   `PUT /teams/{game_id}/{team_id}`
    *   **Описание**: Обновить команду.
    *   **Параметры пути**: `game_id`, `team_id`.
    *   **Тело запроса**: `TeamUpdate`.
    *   **Ответ**: `Team`.
*   `DELETE /teams/{game_id}/{team_id}`
    *   **Описание**: Удалить команду.
    *   **Параметры пути**: `game_id`, `team_id`.
    *   **Ответ**: Статус 204.
*   `POST /teams/{game_id}/{team_id}/players`
    *   **Описание**: Добавить игрока в команду.
    *   **Параметры пути**: `game_id`, `team_id`.
    *   **Тело запроса**: `PlayerTeamAction`.
    *   **Ответ**: `Team`.
*   `DELETE /teams/{game_id}/{team_id}/players/{player_id}`
    *   **Описание**: Удалить игрока из команды.
    *   **Параметры пути**: `game_id`, `team_id`, `player_id`.
    *   **Ответ**: `Team`.
*   `POST /teams/{game_id}/distribute`
    *   **Описание**: Автоматически распределить игроков по командам.
    *   **Параметры пути**: `game_id`.
    *   **Тело запроса**: `TeamDistributionRequest`.
    *   **Ответ**: `List[Team]`.
*   `GET /teams/{game_id}/validate`
    *   **Описание**: Проверить корректность настройки команд.
    *   **Параметры пути**: `game_id`.
    *   **Ответ**: `Dict` с ошибками валидации.

## Эндпоинт здоровья (`/health`)

*   `GET /health`
    *   **Описание**: Проверка статуса сервиса.
    *   **Ответ**: `Dict` с информацией о статусе.