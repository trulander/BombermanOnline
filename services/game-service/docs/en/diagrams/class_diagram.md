[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/diagrams/class_diagram.md)

# Class Diagram (Core Entities)

This diagram illustrates the main game entity classes and their relationships in `game-service`.

```mermaid
classDiagram
    direction RL

    class Entity {
        +str id
        +float x
        +float y
        +float width
        +float height
        +str name
        +bool ai
        +float speed
        +int lives
        +bool invulnerable
        +float invulnerable_timer
        +str color
        +update(float delta_time)
        +draw() dict
    }

    class Inputs {
        <<TypedDict>>
        +bool up
        +bool down
        +bool left
        +bool right
        +bool weapon1
        +bool weapon2
    }

    class Player {
        +UnitType unit_type
        +str team_id
        +tuple direction
        +WeaponType primary_weapon
        +WeaponType secondary_weapon
        +int max_weapons
        +int weapon_power
        +Inputs inputs
        +set_inputs(dict inputs)
        +set_team(str team_id)
        +max_bombs: int
        +bomb_power: int
    }

    class Enemy {
        +EnemyType type
        +float move_timer
        +float change_direction_interval
        +tuple direction
        +bool destroyed
        +float destroy_animation_timer
        +get_random_direction() tuple
    }

    class Weapon {
        <<Abstract>>
        +WeaponType weapon_type
        +str owner_id
        +bool activated
        +float timer
        +activate() None
        +update(float delta_time) None
        +get_damage_area() list
    }

    class Bomb {
        +int power
        +bool exploded
        +float explosion_timer
        +list explosion_cells
    }

    class Bullet {
        +tuple direction
        +float speed
        +bool hit_target
    }

    class Mine {
        +bool exploded
        +bool triggered
        +trigger() None
    }

    class PowerUp {
        +PowerUpType type
        +apply_to_player(Player player) None
    }

    class GameSettings {
        <<Pydantic BaseModel>>
        +int cell_size
        +float player_default_speed
        +float bomb_timer
        +GameModeType game_mode
        +int max_players
        +str map_template_id
        # ... other settings ...
    }
    
    class Map {
        +int width
        +int height
        +ndarray grid
        +list changed_cells
        +get_cell_type(int x, int y) CellType
        +set_cell_type(int x, int y, CellType type)
        +destroy_block(int x, int y) bool
        +get_map() dict
    }

    class UnitType {
        <<Enumeration>>
        BOMBERMAN
        TANK
    }

    class EnemyType {
        <<Enumeration>>
        COIN
        BEAR
        GHOST
    }

    class WeaponType {
        <<Enumeration>>
        BOMB
        BULLET
        MINE
    }

    class PowerUpType {
        <<Enumeration>>
        BOMB_UP
        BOMB_POWER_UP
        SPEED_UP
        LIFE_UP
    }

    class CellType {
        <<Enumeration>>
        EMPTY
        SOLID_WALL
        BREAKABLE_BLOCK
        PLAYER_SPAWN
        ENEMY_SPAWN
        LEVEL_EXIT
    }
    
    class GameModeType {
        <<Enumeration>>
        CAMPAIGN
        FREE_FOR_ALL
        CAPTURE_THE_FLAG
    }

    Entity <|-- Player
    Entity <|-- Enemy
    Entity <|-- Weapon
    Entity <|-- PowerUp
    
    Weapon <|-- Bomb
    Weapon <|-- Bullet
    Weapon <|-- Mine

    Player ..> Inputs : uses
    Player ..> UnitType : has a
    Player ..> WeaponType : uses (primary_weapon, secondary_weapon)
    
    Enemy ..> EnemyType : has a
    
    Weapon ..> WeaponType : has a

    PowerUp ..> PowerUpType : has a
    PowerUp ..> Player : applies to
    
    Map ..> CellType : uses in grid

    GameSettings ..> GameModeType : uses
    
```

**Notation:**
-   `<|--`: Inheritance (e.g., `Player` inherits from `Entity`).
-   `..>`: Association or dependency (e.g., `Player` uses `Inputs`).
-   `<<Abstract>>`: Abstract class.
-   `<<Enumeration>>`: Enumeration.
-   `<<TypedDict>>`: Typed dictionary.
-   `<<Pydantic BaseModel>>`: Pydantic model.
