# NATS События Game Service

Game Service активно использует NATS для асинхронного обмена сообщениями. Это включает получение команд от игроков/других сервисов и отправку обновлений состояния игры.

## 1. Входящие события (Подписки сервиса)

Сервис подписывается на следующие события. Команды обычно отправляются с полем `reply` для получения ответа.

### `game.create`

-   **Описание**: Инициирует создание новой игровой сессии.
-   **Направление**: Клиент/WebAPI -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "уникальный_id_игры_опционально",
      "new_game_settings": { // Опционально, см. GameCreateSettings
        "game_mode": "campaign", // "campaign", "free_for_all", "capture_the_flag"
        "max_players": 4,
        "team_count": 1,
        "player_start_lives": 3,
        "enable_enemies": true,
        "map_chain_id": "id_цепочки_карт_опционально",
        "map_template_id": "id_шаблона_карты_опционально",
        "respawn_enabled": false,
        "friendly_fire": false,
        "time_limit": 300, // секунды
        "score_limit": 10,
        "rounds_count": 15
      }
    }
    ```
    Если `new_game_settings` не предоставлен, то `game_id` обязателен, и игра будет создана с настройками по умолчанию или на основе отдельных полей `game_mode`, `map_template_id`, `map_chain_id` из payload.
-   **Обработчик в Game Service**: `GameCoordinator.game_create()`.
-   **Ответ (на `msg.reply`)**: JSON объект.
    -   Успех: `{"success": true, "game_id": "id_созданной_игры"}`
    -   Ошибка: `{"success": false, "message": "текст_ошибки"}`

### `game.join`

-   **Описание**: Запрос на присоединение игрока к существующей игре.
-   **Направление**: Клиент -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры",
      "player_id": "id_игрока",
      "unit_type": "bomberman" // Опционально, "bomberman" или "tank"
    }
    ```
-   **Обработчик**: `GameCoordinator.game_join()`.
-   **Ответ (на `msg.reply`)**: JSON объект.
    -   Успех: `{"success": true, "player_id": "id_игрока", "game_state": { /* начальное состояние игры */ }}`
    -   Ошибка: `{"success": false, "message": "текст_ошибки"}` (например, "Game not found", "Game is full")

### `game.input`

-   **Описание**: Передача команд ввода от игрока.
-   **Направление**: Клиент -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры",
      "player_id": "id_игрока",
      "inputs": {
        "up": false,
        "down": false,
        "left": true,
        "right": false,
        "weapon1": false, // Основное оружие (бомба/пуля)
        "weapon2": false  // Вторичное оружие (мина)
      }
    }
    ```
-   **Обработчик**: `GameCoordinator.game_input()`.
-   **Ответ**: Обычно нет (fire-and-forget), но если `msg.reply` указан, сервис отправит `null` или пустой ответ при успехе, или ошибку.

### `game.place_bomb` (Устаревшее, используйте `game.apply_weapon`)

-   **Описание**: Команда на установку бомбы игроком.
-   **Направление**: Клиент -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры",
      "player_id": "id_игрока"
    }
    ```
-   **Обработчик**: `GameCoordinator.game_place_bomb()` (внутренне вызывает `game.apply_weapon` с типом бомбы).
-   **Ответ (на `msg.reply`)**: `{"success": true/false, "message": "опционально_сообщение"}`.

### `game.apply_weapon`

-   **Описание**: Универсальная команда на применение оружия игроком.
-   **Направление**: Клиент -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры",
      "player_id": "id_игрока",
      "weapon_type": "bomb" // "bomb", "bullet", "mine". Опционально, по умолчанию основное оружие игрока.
    }
    ```
-   **Обработчик**: `GameCoordinator.game_apply_weapon()`.
-   **Ответ (на `msg.reply`)**: `{"success": true/false, "message": "опционально_сообщение"}`.

### `game.get_state`

-   **Описание**: Запрос на получение текущего полного состояния игры.
-   **Направление**: Клиент -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры"
    }
    ```
-   **Обработчик**: `GameCoordinator.game_get_state()`.
-   **Ответ (на `msg.reply`)**: JSON объект.
    -   Успех: `{"success": true, "game_state": { /* текущее состояние игры */ }, "full_map": { /* полная карта */ }}`
    -   Ошибка: `{"success": false, "message": "текст_ошибки"}`

### `game.disconnect`

-   **Описание**: Уведомление об отключении игрока от игры.
-   **Направление**: Клиент/WebAPI -> Game Service.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "game_id": "id_игры",
      "player_id": "id_игрока"
    }
    ```
-   **Обработчик**: `GameCoordinator.game_player_disconnect()`.
-   **Ответ (на `msg.reply`)**: `{"success": true/false, "message": "опционально_сообщение"}`.

## 2. Исходящие события (Публикации сервиса)

Сервис публикует следующие события для уведомления клиентов и других систем.

### `game.update.{game_id}`

-   **Описание**: Регулярное обновление состояния игры.
-   **Направление**: Game Service -> Клиенты.
-   **Данные (Payload)**: JSON объект, представляющий текущее состояние игры (см. `GameModeService.get_state()` для структуры).
    Пример ключевых полей:
    ```json
    {
      "players": { /* ... */ },
      "teams": { /* ... */ },
      "enemies": [ /* ... */ ],
      "weapons": [ /* ... */ ],
      "powerUps": [ /* ... */ ],
      "map": {
        "width": 23,
        "height": 23,
        "changedCells": [{"x": 1, "y": 2, "type": 0}],
        "cellSize": 40
      },
      "score": 0,
      "level": 1,
      "gameOver": false,
      "status": "active",
      "gameMode": "campaign"
    }
    ```
-   **Источник**: Публикуется из `GameCoordinator.start_game_loop()`.

### `game.over.{game_id}`

-   **Описание**: Уведомление об окончании игровой сессии.
-   **Направление**: Game Service -> Клиенты.
-   **Данные (Payload)**: Пустой JSON объект `{}`.
-   **Источник**: Публикуется из `GameCoordinator.start_game_loop()`, когда игра становится неактивной.

### `game.player_disconnected.{game_id}`

-   **Описание**: Уведомление других игроков о том, что один из игроков отключился.
-   **Направление**: Game Service -> Клиенты.
-   **Данные (Payload)**: JSON объект.
    ```json
    {
      "player_id": "id_отключившегося_игрока"
    }
    ```
-   **Источник**: Публикуется из `EventService.handle_player_disconnect()` после успешной обработки отключения. 