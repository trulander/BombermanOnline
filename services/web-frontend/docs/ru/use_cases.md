# Сценарии использования (Детальный обзор)

Этот документ описывает ключевые сценарии взаимодействия пользователя с системой, иллюстрируя их с помощью подробных диаграмм последовательности.

## 1. Аутентификация

### UC-1: Регистрация нового пользователя

*   **Описание:** Новый пользователь создает учетную запись.

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Frontend as Фронтенд (React)
    participant AuthService as Auth Service

    User->>Frontend: Открывает /account/register
    User->>Frontend: Заполняет и отправляет форму (username, email, password)
    Frontend->>AuthService: POST /users (с данными формы)
    alt Успешная регистрация
        AuthService->>AuthService: Создает пользователя в БД, отправляет email
        AuthService-->>Frontend: HTTP 201 Created
        Frontend->>User: Показывает сообщение об успехе
    else Ошибка (например, email занят)
        AuthService-->>Frontend: HTTP 4xx/5xx
        Frontend->>User: Показывает сообщение об ошибке
    end
```

### UC-2: Вход в систему

*   **Описание:** Зарегистрированный пользователь входит в свою учетную запись.

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Frontend as Фронтенд (React)
    participant AuthService as Auth Service

    User->>Frontend: Открывает /account/login, вводит данные
    Frontend->>AuthService: POST /auth/login (username, password)
    AuthService-->>Frontend: { access_token, refresh_token }
    Frontend->>Frontend: tokenService.saveTokens() (в localStorage и cookie `ws_auth_token`)
    Frontend->>AuthService: GET /users/me (с новым токеном)
    AuthService-->>Frontend: { id, username, ... }
    Frontend->>Frontend: Сохраняет данные пользователя в AuthContext
    Frontend->>User: Перенаправляет на /account/dashboard
```

## 2. Управление игрой

### UC-3: Создание и запуск игры

*   **Описание:** Игрок создает игру, присоединяется к ней и запускает ее.

```mermaid
sequenceDiagram
    participant Player as Игрок
    participant Frontend as Фронтенд
    participant WebAPIService as WebAPI Service

    Player->>Frontend: Открывает /account/games/create, выбирает настройки
    Frontend->>WebAPIService: POST /games (с настройками)
    WebAPIService-->>Frontend: { game_id }
    Frontend->>Player: Перенаправляет на /account/game/{game_id}
    Frontend->>Frontend: В ManageGame нажимает "Присоединиться к игре"
    Frontend->>WebAPIService: POST /game-service/games/api/v1/players (через прокси)
    WebAPIService-->>Frontend: { success: true }
    Player->>Frontend: Нажимает "Начать игру"
    Frontend->>WebAPIService: PUT /game-service/games/api/v1/status (action: 'start')
    WebAPIService-->>Frontend: { success: true }
    Frontend->>Player: Обновляет статус игры на "Активна"
```

### UC-4: Присоединение к игре из списка

*   **Описание:** Игрок видит список игр и присоединяется к одной из них.

```mermaid
sequenceDiagram
    participant Player as Игрок
    participant Frontend as Фронтенд
    participant WebAPIService as WebAPI Service
    participant GameService as Game Service

    Player->>Frontend: Открывает /account/games
    Frontend->>WebAPIService: GET /games
    WebAPIService-->>Frontend: [ { game_id, status, ... } ]
    Player->>Frontend: Нажимает "Присоединиться" для игры X
    Frontend->>Player: Переходит на /account/game/X
    Frontend->>WebAPIService: Устанавливает WebSocket соединение
    WebAPIService-->>Frontend: Соединение установлено
    Frontend->>WebAPIService: emit('join_game', { game_id: X, player_id: user.id })
    WebAPIService->>GameService: (NATS) join_game
    GameService-->>WebAPIService: (NATS) game_state
    WebAPIService-->>Frontend: emit('game_state', { ... })
    Frontend->>Player: Отрисовывает игровое поле
```

### UC-5: Игрок покидает игру

*   **Описание:** Игрок, находясь в лобби, решает покинуть игру.

```mermaid
sequenceDiagram
    participant Player as Игрок
    participant Frontend as Фронтенд
    participant WebAPIService as WebAPI Service

    Player->>Frontend: В окне ManageGame нажимает "Покинуть игру"
    Frontend->>WebAPIService: DELETE /game-service/games/api/v1/players/{user.id} (через прокси)
    alt Успешное удаление
        WebAPIService-->>Frontend: { success: true }
        Frontend->>Frontend: Обновляет состояние (isPlayerInThisGame = false)
        Frontend->>Player: Показывает кнопку "Присоединиться к игре"
    else Ошибка
        WebAPIService-->>Frontend: HTTP 4xx/5xx
        Frontend->>Player: Показывает сообщение об ошибке
    end
```

## 3. Игровой процесс

### UC-6: Установка бомбы

*   **Описание:** Игрок нажимает пробел, чтобы установить бомбу.

```mermaid
sequenceDiagram
    participant Player as Игрок
    participant Browser as Браузер
    participant InputHandler as InputHandler.ts
    participant GameClient as GameClient.ts
    participant WebAPIService as WebAPI Service

    Player->>Browser: Нажимает клавишу "Пробел"
    Browser->>InputHandler: keydown event
    InputHandler->>InputHandler: this.input.weapon1 = true
    GameClient->>InputHandler: В игровом цикле вызывает getInput()
    GameClient->>WebAPIService: emit('place_weapon', { game_id, weapon_action: 'PLACEWEAPON1' })
    InputHandler->>InputHandler: resetWeaponInput() -> this.input.weapon1 = false
```

### UC-7: Автоматическое обновление токена в игре

*   **Описание:** У игрока во время игры истекает `accessToken`. Клиент должен незаметно его обновить, не прерывая игровой процесс.

```mermaid
sequenceDiagram
    participant GameClient as GameClient.ts
    participant SocketIO as Socket.IO
    participant WebAPIService as WebAPI Service
    participant AuthService as Auth Service

    GameClient->>SocketIO: Попытка отправки события (например, 'input')
    SocketIO->>WebAPIService: Отправляет событие
    WebAPIService->>WebAPIService: Проверяет токен и обнаруживает, что он истек
    WebAPIService-->>GameClient: emit('auth_error', { message: 'Token expired' })

    GameClient->>GameClient: Вызывает handleAuthError()
    GameClient->>AuthService: (через fetch) POST /auth/refresh (с refresh_token)
    AuthService-->>GameClient: { access_token, ... }
    GameClient->>GameClient: tokenService.saveTokens() (обновляет localStorage и cookie)
    GameClient->>SocketIO: socket.disconnect()
    GameClient->>SocketIO: socket.connect() (с новым токеном в cookie)
```

## 4. Редактор карт

### UC-8: Создание и сохранение шаблона карты

*   **Описание:** Пользователь создает новый шаблон карты с помощью интерактивного редактора.

```mermaid
sequenceDiagram
    participant User as Пользователь
    participant Frontend as Фронтенд (MapEditor.tsx)
    participant GameServiceAPI as Game Service API

    User->>Frontend: Нажимает "Создать новый шаблон"
    Frontend->>User: Открывает диалог с пустой сеткой
    User->>Frontend: Вводит название, выбирает тип ячейки "Стена"
    User->>Frontend: "Рисует" стены на сетке, зажав мышь
    Frontend->>Frontend: Обновляет локальное состояние `currentGrid` при каждом движении мыши
    User->>Frontend: Нажимает "Создать"
    Frontend->>GameServiceAPI: POST /maps/templates (с названием и `grid_data`)
    GameServiceAPI-->>Frontend: { id: "map123", ... }
    Frontend->>Frontend: fetchMapTemplates() для обновления списка
    Frontend->>User: Закрывает диалог и показывает новую карту в списке
```
