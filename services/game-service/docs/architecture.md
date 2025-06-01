# Архитектура Game Service

## Диаграмма компонентов

```mermaid
graph TB
    subgraph "Game Service"
        subgraph "Coordinators"
            GC[GameCoordinator]
        end
        
        subgraph "Services"
            GS[GameService]
            MS[MapService]
            NS[NatsService]
            DS[DatabaseService]
        end
        
        subgraph "Repositories"
            MR[MapRepository]
        end
        
        subgraph "Entities"
            GM[Map]
            GP[Player]
            GE[Enemy]
            GB[Bomb]
            GPU[PowerUp]
            GST[GameSettings]
            GMD[GameMode]
        end
        
        subgraph "Models"
            MT[MapTemplate]
            MG[MapGroup]
            MC[MapChain]
        end
    end
    
    subgraph "External Services"
        PG[(PostgreSQL)]
        RD[(Redis)]
        NT[NATS]
    end
    
    GC --> GS
    GC --> NS
    GC --> DS
    
    GS --> MS
    GS --> GP
    GS --> GE
    GS --> GB
    GS --> GPU
    GS --> GST
    
    MS --> MR
    MS --> GM
    MS --> GST
    
    DS --> PG
    DS --> RD
    
    MR --> PG
    MR --> RD
    MR --> MT
    MR --> MG
    MR --> MC
    
    NS --> NT
```

## Диаграмма классов

```mermaid
classDiagram
    class GameCoordinator {
        -notification_service: NatsService
        -games: dict[str, GameService]
        -map_repository: MapRepository
        +initialize_handlers()
        +start_game_loop()
        +game_create(**kwargs)
        +game_join(**kwargs)
        +game_input(**kwargs)
        +game_place_bomb(**kwargs)
    }
    
    class GameService {
        -settings: GameSettings
        -map_service: MapService
        -players: dict[str, Player]
        -enemies: list[Enemy]
        -bombs: dict[str, Bomb]
        -power_ups: dict[str, PowerUp]
        -map: Map
        +add_player(player: Player): bool
        +update(): dict
        +place_bomb(player: Player): bool
    }
    
    class MapService {
        -map_repository: MapRepository
        -game_settings: GameSettings
        +create_map_from_template(template_id: str): Map
        +generate_random_map(width: int, height: int): Map
        +get_empty_cells(map: Map): list[tuple]
        +generate_enemies_for_level(map: Map, level: int): list
    }
    
    class MapRepository {
        -db_pool: asyncpg.Pool
        -redis_client: redis.Redis
        +get_map_template(map_id: str): MapTemplate
        +get_map_group(group_id: str): MapGroup
        +get_map_chain(chain_id: str): MapChain
    }
    
    class GameSettings {
        +cell_size: int
        +default_map_width: int
        +default_map_height: int
        +fps: float
        +game_mode: GameModeSettings
        +player_start_lives: int
        +bomb_timer: float
    }
    
    class GameModeSettings {
        +mode_type: GameModeType
        +max_players: int
        +enable_enemies: bool
        +map_chain_id: str
        +map_group_id: str
    }
    
    class Map {
        +width: int
        +height: int
        +grid: np.ndarray
        +changed_cells: list
        +get_cell_type(x: int, y: int): CellType
        +set_cell_type(x: int, y: int, type: CellType)
        +destroy_block(x: int, y: int): bool
    }
    
    class Entity {
        +x: float
        +y: float
        +width: float
        +height: float
        +id: str
        +lives: int
        +update(delta_time: float)
    }
    
    class Player {
        +max_bombs: int
        +bomb_power: int
        +inputs: PlayerInputs
        +set_inputs(inputs: dict)
    }
    
    class Enemy {
        +type: EnemyType
        +direction: tuple
        +destroyed: bool
        +get_random_direction(): tuple
    }
    
    GameCoordinator --> GameService
    GameCoordinator --> DatabaseService
    GameCoordinator --> NatsService
    
    GameService --> MapService
    GameService --> GameSettings
    GameService --> Map
    GameService --> Player
    GameService --> Enemy
    
    MapService --> MapRepository
    MapService --> GameSettings
    
    MapRepository --> MapTemplate
    MapRepository --> MapGroup
    MapRepository --> MapChain
    
    GameSettings --> GameModeSettings
    
    Player --|> Entity
    Enemy --|> Entity
    Bomb --|> Entity
    PowerUp --|> Entity
```

## Диаграмма последовательности создания игры

```mermaid
sequenceDiagram
    participant C as Client
    participant GC as GameCoordinator
    participant GS as GameService
    participant MS as MapService
    participant MR as MapRepository
    participant DB as PostgreSQL
    participant R as Redis
    
    C->>GC: game_create(game_id, mode, map_template_id)
    GC->>GC: create GameSettings
    GC->>MS: new MapService(repository, settings)
    GC->>GS: new GameService(settings, map_service)
    
    GS->>MS: create_map_from_template(template_id)
    MS->>MR: get_map_template(template_id)
    
    alt Template in cache
        MR->>R: get cached template
        R-->>MR: template data
    else Template not cached
        MR->>DB: fetch template
        DB-->>MR: template data
        MR->>R: cache template
    end
    
    MR-->>MS: MapTemplate
    MS->>MS: create Map from template
    MS-->>GS: Map instance
    
    alt Enemies enabled
        GS->>MS: generate_enemies_for_level(map, level)
        MS->>MS: get_enemy_spawn_positions(map)
        MS-->>GS: enemies data
        GS->>GS: create Enemy instances
    end
    
    GS-->>GC: GameService ready
    GC-->>C: game created
```

## Диаграмма состояний игры

```mermaid
stateDiagram-v2
    [*] --> Created: game_create
    Created --> WaitingPlayers: ready
    WaitingPlayers --> InProgress: min_players_joined
    InProgress --> LevelComplete: all_enemies_defeated
    LevelComplete --> InProgress: next_level_loaded
    InProgress --> GameOver: all_players_dead
    GameOver --> [*]: cleanup
    
    WaitingPlayers --> GameOver: timeout
    InProgress --> GameOver: timeout
```

## Принципы архитектуры

### SOLID принципы

1. **Single Responsibility Principle (SRP)**
   - `MapService` отвечает только за управление картами
   - `GameService` - за игровую логику
   - `MapRepository` - за доступ к данным карт

2. **Open/Closed Principle (OCP)**
   - Новые игровые режимы добавляются через `GameModeType`
   - Новые типы сущностей наследуются от `Entity`

3. **Liskov Substitution Principle (LSP)**
   - Все игровые сущности наследуют от `Entity`
   - Могут использоваться взаимозаменяемо

4. **Interface Segregation Principle (ISP)**
   - Разделение интерфейсов для разных типов операций
   - Репозиторий не зависит от игровой логики

5. **Dependency Inversion Principle (DIP)**
   - `GameService` зависит от абстракции `MapService`
   - Инъекция зависимостей через конструкторы

### Чистая архитектура

- **Entities** - бизнес-сущности (Player, Enemy, Map)
- **Use Cases** - бизнес-логика (GameService, MapService)
- **Interface Adapters** - репозитории и контроллеры
- **Frameworks** - внешние зависимости (PostgreSQL, Redis, NATS)

### Разделение ответственности

- **GameCoordinator** - оркестрация игр и обработка событий
- **GameService** - основная игровая логика
- **MapService** - генерация и управление картами
- **MapRepository** - доступ к данным карт
- **DatabaseService** - управление подключениями к БД