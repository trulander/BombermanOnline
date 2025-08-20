# Справка по API
[![English](https://img.shields.io/badge/lang-English-blue)](../en/api.md)

Этот документ описывает все доступные эндпоинты RESTful API и события WebSocket, предоставляемые `WebAPI Service`.

## RESTful API

Все эндпоинты API доступны по префиксу `/api/v1`.

### Ресурс: Игры (`/games`)

#### `POST /games`

Создает новую игровую сессию.

*   **Описание**: Инициирует процесс создания новой игры. Сервис отправляет команду в NATS, и `Game Allocator Service` выделяет для игры экземпляр `Game Service`. Фактическое создание происходит асинхронно.
*   **Тело запроса**: `GameCreateSettings` (JSON)

    ```json
    {
      "game_mode": "CAMPAIGN",
      "max_players": 4,
      "player_start_lives": 3,
      "enable_enemies": true,
      "map_chain_id": null,
      "map_template_id": null,
      "respawn_enabled": false,
      "friendly_fire": false,
      "time_limit": 300,
      "score_limit": 10,
      "rounds_count": 15
    }
    ```
*   **Успешный ответ (200 OK)**:

    ```json
    {
      "success": true,
      "game_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef"
    }
    ```
*   **Ответ с ошибкой (500 Internal Server Error)**:

    ```json
    {
      "detail": "Сообщение об ошибке от сервиса"
    }
    ```

### Ресурс: Прокси для Game Service (`/game-service`)

#### `ANY /game-service/{game_id}/{path:path}`

Универсальный прокси-эндпоинт для взаимодействия с `Game Service`.

*   **Описание**: Этот эндпоинт перенаправляет любой HTTP-запрос (GET, POST, PUT, DELETE и т.д.) на экземпляр `Game Service`, который обслуживает указанную игру. `WebAPI Service` находит адрес нужного экземпляра в кэше (Redis) и полностью проксирует запрос, включая метод, заголовки, параметры и тело.
*   **Параметры пути**:
    *   `game_id` (string, required): Уникальный идентификатор игры.
    *   `path` (string, required): Путь, который будет передан в `Game Service`. Например, если вы делаете запрос на `/api/v1/game-service/a1b2c3/players/p1`, то в `Game Service` будет передан запрос на `/players/p1`.
*   **Ответы**:
    *   **2xx/4xx/5xx**: Ответ полностью соответствует тому, что вернул `Game Service`.
    *   **404 Not Found**: Возвращается, если `game_id` не найден в кэше (игра не существует или уже завершена).
    *   **503 Service Unavailable**: Возвращается, если `Game Service` недоступен.

## WebSocket API (Socket.IO)

WebSocket-сервер доступен по пути `/socket.io`. Клиент должен установить соединение и затем обмениваться событиями.

### События, отправляемые клиентом (Client -> Server)

#### `join_game`

Присоединяет клиента к игровой комнате.

*   **Данные (Payload)**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "player_id": "p1-xyz..." // опционально
    }
    ```
*   **Ответ (Callback)**: Возвращает результат операции.

    ```json
    {
      "success": true,
      "player_id": "p1-xyz...",
      "message": null
    }
    ```

#### `input`

Отправляет на сервер состояние органов управления игрока.

*   **Данные (Payload)**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "inputs": {
        "up": true,
        "down": false,
        "left": false,
        "right": false
      }
    }
    ```

#### `place_weapon`

Отправляет команду на использование оружия (например, установка бомбы).

*   **Данные (Payload)**:

    ```json
    {
      "game_id": "a1b2c3d4-...",
      "weapon_type": "bomb"
    }
    ```
*   **Ответ (Callback)**: Возвращает результат (например, успешно ли установлена бомба).

    ```json
    {
      "success": true,
      "message": "Бомба установлена"
    }
    ```

#### `get_game_state`

Запрашивает полное текущее состояние игры.

*   **Данные (Payload)**:

    ```json
    {
      "game_id": "a1b2c3d4-..."
    }
    ```
*   **Ответ (Callback)**: Возвращает полное состояние игры.

### События, получаемые клиентом (Server -> Client)

#### `game_update`

Сервер присылает это событие, когда состояние игры изменяется.

*   **Данные (Payload)**: `GameState` - объект, содержащий информацию о позициях игроков, врагов, бомб и т.д.

#### `game_over`

Сервер присылает это событие, когда игра завершена.

*   **Данные (Payload)**: Пустой объект `{}`.

#### `player_disconnected`

Сервер присылает это событие, когда один из игроков отключается.

*   **Данные (Payload)**:

    ```json
    {
      "player_id": "p2-abc..."
    }
    ```
