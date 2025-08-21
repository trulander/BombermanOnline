[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/architecture/models.md)

# Data Models

This section describes the data models used in the game service. This includes Pydantic models for API data validation and game creation settings, as well as SQLAlchemy models for defining the structure of tables in the database.

## 1. SQLAlchemy ORM Models

These models define the structure of the tables in the PostgreSQL database used by the game service. They are designed using the SQLAlchemy ORM.

### 1.1. `MapTemplateORM`

Represents the `map_templates` table, which stores game map templates.

- **Fields:**
    - `id` (String, Primary Key): Unique identifier for the map template.
    - `name` (String): Name of the map template.
    - `description` (Text, Optional): Description of the map template.
    - `width` (Integer): Width of the map in cells.
    - `height` (Integer): Height of the map in cells.
    - `grid_data` (JSON): A 2D array (list of lists of numbers) representing the map grid and the placement of elements on it.
    - `difficulty` (Integer): Difficulty level of the map (1-10).
    - `max_players` (Integer): Maximum number of players (1-8).
    - `min_players` (Integer): Minimum number of players (>=1).
    - `estimated_play_time` (Integer): Approximate playing time on the map in seconds.
    - `tags` (JSON, Optional): List of tags for classifying the map.
    - `created_by` (String): Identifier of the user who created the template.
    - `created_at` (DateTime): Date and time of creation.
    - `updated_at` (DateTime): Date and time of the last update.
    - `is_active` (Boolean): Flag for template activity.

### 1.2. `MapGroupORM`

Represents the `map_groups` table, which groups several map templates together.

- **Fields:**
    - `id` (String, Primary Key): Unique identifier for the map group.
    - `name` (String): Name of the map group.
    - `description` (Text, Optional): Description of the map group.
    - `map_ids` (JSON): List of map template identifiers (`MapTemplateORM.id`) included in the group.
    - `created_by` (String): Identifier of the user who created the group.
    - `created_at` (DateTime): Date and time of creation.
    - `updated_at` (DateTime): Date and time of the last update.
    - `is_active` (Boolean): Flag for group activity.

### 1.3. `MapChainORM`

Represents the `map_chains` table, which defines a sequence of maps (a chain) for progression, possibly with increasing difficulty.

- **Fields:**
    - `id` (String, Primary Key): Unique identifier for the map chain.
    - `name` (String): Name of the map chain.
    - `description` (Text, Optional): Description of the map chain.
    - `map_ids` (JSON): List of map template identifiers (`MapTemplateORM.id`) that make up the chain.
    - `difficulty_progression` (Float): Difficulty progression coefficient for maps in the chain.
    - `created_by` (String): Identifier of the user who created the chain.
    - `created_at` (DateTime): Date and time of creation.
    - `updated_at` (DateTime): Date and time of the last update.
    - `is_active` (Boolean): Flag for chain activity.

## 2. Pydantic Models

These models are used for data validation in HTTP API requests and responses, as well as for defining the structure of settings when creating a game.

### 2.1. Map API Models

These models are defined in `app/models/map_models.py`.

#### 2.1.1. Map Templates (`MapTemplate`)

-   **`MapTemplateBase`**: Base model for a map template.
    -   `name` (str): Name.
    -   `description` (Optional[str]): Description.
    -   `width` (int): Width (5-50).
    -   `height` (int): Height (5-50).
    -   `grid_data` (List[List[int]]): Map grid data.
    -   `difficulty` (int): Difficulty (1-10).
    -   `max_players` (int): Max. players (1-8).
    -   `min_players` (int): Min. players (>=1).
    -   `estimated_play_time` (int): Approximate game time (in seconds, >=60).
    -   `tags` (List[str]): Tags.
-   **`MapTemplateCreate`**: Model for creating a new map template (inherits from `MapTemplateBase`).
-   **`MapTemplateUpdate`**: Model for updating an existing map template (all fields are optional).
-   **`MapTemplate`**: Model for representing a map template in API responses (includes `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Has `from_attributes = True` configuration for working with ORM objects.
    -   Contains a `from_orm` method for converting a `MapTemplateORM` object.

#### 2.1.2. Map Groups (`MapGroup`)

-   **`MapGroupBase`**: Base model for a map group.
    -   `name` (str): Name.
    -   `description` (Optional[str]): Description.
    -   `map_ids` (List[str]): List of map template IDs (at least 1 element).
-   **`MapGroupCreate`**: Model for creating a new map group (inherits from `MapGroupBase`).
-   **`MapGroupUpdate`**: Model for updating an existing map group (all fields are optional).
-   **`MapGroup`**: Model for representing a map group in API responses (includes `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Has `from_attributes = True` configuration.
    -   Contains a `from_orm` method for converting a `MapGroupORM` object.

#### 2.1.3. Map Chains (`MapChain`)

-   **`MapChainBase`**: Base model for a map chain.
    -   `name` (str): Name.
    -   `description` (Optional[str]): Description.
    -   `map_ids` (List[str]): List of map template IDs (at least 1 element).
    -   `difficulty_progression` (float): Difficulty progression coefficient (0.1-5.0).
-   **`MapChainCreate`**: Model for creating a new map chain (inherits from `MapChainBase`).
-   **`MapChainUpdate`**: Model for updating an existing map chain (all fields are optional).
-   **`MapChain`**: Model for representing a map chain in API responses (includes `id`, `created_by`, `created_at`, `updated_at`, `is_active`).
    -   Has `from_attributes = True` configuration.
    -   Contains a `from_orm` method for converting a `MapChainORM` object.

### 2.2. Team API Models

These models are defined in `app/models/team_models.py` and are used for managing teams via the REST API.

#### 2.2.1. Teams (`Team`)

-   **`TeamBase`**: Base model for a team.
    -   `name` (str): Team name (1-50 characters).

-   **`TeamCreate`**: Model for creating a new team (inherits from `TeamBase`).

-   **`TeamUpdate`**: Model for updating an existing team.
    -   `name` (Optional[str]): New team name (1-50 characters).

-   **`Team`**: Model for representing a team in API responses.
    -   `id` (str): Unique team identifier.
    -   `name` (str): Team name.
    -   `score` (int): Team score (default 0).
    -   `player_ids` (List[str]): List of player IDs in the team.
    -   `player_count` (int): Number of players in the team (default 0).
    -   Has `from_attributes = True` configuration for working with entity objects.

#### 2.2.2. Player Actions in Teams

-   **`PlayerTeamAction`**: Model for adding/removing a player from a team.
    -   `player_id` (str): Player ID.

-   **`TeamDistributionRequest`**: Model for automatically distributing players among teams.
    -   `redistribute_existing` (bool): Redistribute existing players (default False).

### 2.3. Filter Models for Map API

These models are defined in `app/models/map_models.py` and are used for filtering lists in API requests.

-   **`MapTemplateFilter`**: Filters for searching map templates.
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
-   **`MapGroupFilter`**: Filters for searching map groups.
    -   `name` (Optional[str])
    -   `created_by` (Optional[str])
    -   `is_active` (Optional[bool], default: True)
    -   `limit` (int, default: 20, 1-100)
    -   `offset` (int, default: 0, >=0)
-   **`MapChainFilter`**: Filters for searching map chains.
    -   `name` (Optional[str])
    -   `created_by` (Optional[str])
    -   `is_active` (Optional[bool], default: True)
    -   `limit` (int, default: 20, 1-100)
    -   `offset` (int, default: 0, >=0)

### 2.4. Game Creation Models

This model is defined in `app/models/game_create_models.py`.

-   **`GameCreateSettings`**: Defines the settings for creating a new game session.
    -   `game_id` (Optional[str]): Game ID (can be assigned later).
    -   `game_mode` (`GameModeType`): Game mode (e.g., `CAMPAIGN`).
    -   `max_players` (int): Maximum number of players.
    -   `team_count` (int): Number of teams.
    -   `player_start_lives` (int): Initial number of lives for a player.
    -   `enable_enemies` (bool): Whether enemies are enabled.
    -   `map_chain_id` (Optional[str]): ID of the map chain.
    -   `map_template_id` (Optional[str]): ID of the map template.
    -   `respawn_enabled` (bool): Whether respawn is enabled.
    -   `friendly_fire` (bool): Whether friendly fire is enabled.
    -   `time_limit` (Optional[int]): Time limit for the game in seconds.
    -   `score_limit` (Optional[int]): Score limit to win.
    -   `rounds_count` (Optional[int]): Number of rounds.
