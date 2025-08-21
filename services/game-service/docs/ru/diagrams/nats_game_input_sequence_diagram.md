[![English](https://img.shields.io/badge/lang-English-blue)](../../en/diagrams/nats_game_input_sequence_diagram.md)

# Диаграмма Последовательности: Обработка `game.input`

Эта диаграмма показывает последовательность вызовов и взаимодействий компонентов при обработке NATS-события `game.input`.

```mermaid
sequenceDiagram
    participant Client
    participant NATS_Server
    participant EventService
    participant GameCoordinator
    participant GameService
    participant Player
    participant GameModeService

    Client->>NATS_Server: publish(subject="game.input", data={game_id, player_id, inputs})
    NATS_Server->>EventService: on_message(msg)
    EventService->>GameCoordinator: game_input_handler(decoded_payload)
    GameCoordinator->>GameService: get_game_by_id(game_id)
    Note over GameCoordinator: Находит нужный экземпляр GameService
    GameCoordinator->>Player: get_player_by_id(player_id)
    Note over GameCoordinator: Находит нужный экземпляр Player в GameService
    GameCoordinator->>Player: set_inputs(inputs)
    Player->>Player: Обновляет self.inputs
    opt UnitType is TANK
        Player->>Player: Обновляет self.direction
    end
    
    Note right of GameCoordinator: Далее, в игровом цикле (GameCoordinator.start_game_loop):
    GameCoordinator->>GameService: update(delta_time)
    GameService->>GameModeService: update(delta_time)
    GameModeService->>Player: Движение игрока на основе Player.inputs
    GameModeService->>GameModeService: Проверка столкновений, другая логика
    GameModeService-->>GameService: updated_state
    GameService-->>GameCoordinator: updated_state
    GameCoordinator->>EventService: send_game_update(game_id, updated_state)
    EventService->>NATS_Server: publish(subject="game.update.{game_id}", data=updated_state)
    NATS_Server->>Client: on_message(updated_state)

```

**Описание шагов:**

1.  **Клиент** публикует сообщение `game.input` в **NATS_Server**. Сообщение содержит `game_id`, `player_id` и состояние кнопок ввода (`inputs`).
2.  **NATS_Server** доставляет это сообщение подписчику — **EventService**.
3.  **EventService** получает сырое сообщение, декодирует его JSON-содержимое и вызывает соответствующий обработчик в **GameCoordinator** (`game_input_handler`).
4.  **GameCoordinator** по `game_id` находит нужный экземпляр **GameService** (управляющий конкретной игровой сессией).
5.  **GameCoordinator** по `player_id` находит объект **Player** внутри этого **GameService**.
6.  **GameCoordinator** вызывает метод `player.set_inputs(inputs)`, передавая новые состояния кнопок.
7.  Объект **Player** обновляет свое внутреннее состояние `self.inputs`. Если игрок типа `TANK`, также обновляется его атрибут `self.direction` на основе нажатых клавиш движения (вверх, вниз, влево, вправо).
8.  Далее, в рамках основного игрового цикла (`start_game_loop` в **GameCoordinator**), который выполняется периодически:
    -   **GameCoordinator** вызывает `update(delta_time)` у соответствующего **GameService**.
    -   **GameService** делегирует вызов `update(delta_time)` своему текущему **GameModeService**.
    -   **GameModeService** обрабатывает логику обновления, включая:
        -   Перемещение объекта **Player** на основе его обновленного состояния `Player.inputs` и `Player.direction`.
        -   Проверку столкновений, применение физики и другую игровую логику.
    -   **GameModeService** возвращает обновленное состояние игры в **GameService**.
    -   **GameService** возвращает его в **GameCoordinator**.
9.  **GameCoordinator** через **EventService** публикует событие `game.update.{game_id}` в **NATS_Server** с полным обновленным состоянием игры.
10. **NATS_Server** доставляет это обновление всем подписанным **Клиентам**.