[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/configuration.md)

# Game Service Configuration

The Game Service is configured both at the application level (via environment variables) and at the level of each individual game session (upon its creation).

## 1. Global Service Settings (Environment Variables)

These settings are defined via environment variables and determine the behavior of the entire service. The `.env` file (created from `.env-example`) is used to set them.

**Key Environment Variables:**

| Variable                     | Description                                                                 | Default (`app/config.py`)         |
| :----------------------------- | :----------------------------------------------------------------------- | :------------------------------------- |
| `API_V1_STR`                   | URL prefix for all V1 API endpoints.                                  | `/games/api/v1`                        |
| `APP_TITLE`                    | Application title (used in Swagger).                           | `Bomberman Game Service`               |
| `HOST`                         | Host on which the FastAPI application runs.                         | `0.0.0.0`                              |
| `PORT`                         | Port on which the FastAPI application runs.                         | `5002`                                 |
| `DEBUG`                        | Enables FastAPI debug mode.                                          | `True`                                 |
| `RELOAD`                       | Enables Uvicorn automatic reload on code changes.        | `True`                                 |
| `SWAGGER_URL`                  | URL for accessing Swagger UI documentation.                               | `/games/docs`                          |
| `CORS_ORIGINS`                 | List of allowed origins for CORS (comma-separated or JSON list).  | `["*"]` (all origins)              |
| `CORS_CREDENTIALS`             | Whether CORS allows credentials (e.g., cookies).               | `True`                                 |
| `CORS_METHODS`                 | List of allowed HTTP methods for CORS.                                | `["*"]` (all methods)                 |
| `CORS_HEADERS`                 | List of allowed HTTP headers for CORS.                             | `["*"]` (all headers)                 |
| `POSTGRES_HOST`                | PostgreSQL database host.                                               | `localhost`                            |
| `POSTGRES_PORT`                | PostgreSQL database port.                                               | `5432`                                 |
| `POSTGRES_DB`                  | PostgreSQL database name.                                              | `game_service`                         |
| `POSTGRES_USER`                | Username for connecting to PostgreSQL.                           | `bomberman`                            |
| `POSTGRES_PASSWORD`            | Password for connecting to PostgreSQL.                                     | `bomberman`                            |
| `REDIS_HOST`                   | Redis server host.                                                      | `localhost`                            |
| `REDIS_PORT`                   | Redis server port.                                                      | `6379`                                 |
| `REDIS_DB`                     | Redis database number.                                                 | `0`                                    |
| `REDIS_PASSWORD`               | Password for connecting to Redis (if required).                         | `None`                                 |
| `NATS_URL`                     | URL for connecting to the NATS server.                                      | `nats://localhost:4222`                |
| `LOG_LEVEL`                    | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL).             | `INFO`                                 |
| `LOG_FORMAT`                   | Log format (`text` or `json`).                                        | `text`                                 |
| `TRACE_CALLER`                 | Whether to add caller function information to JSON logs.     | `True`                                 |
| `GAME_UPDATE_FPS`              | Target game loop update frequency (in frames per second).          | `30.0`                                 |
| `GAME_OVER_TIMEOUT`            | Timeout before actually removing a finished game from memory (in seconds). | `5.0`                                  |

**Computed Variables (in `app/config.py`):**

-   `DATABASE_URI`: Full URI for connecting to PostgreSQL (synchronous, for Alembic).
-   `ASYNC_DATABASE_URI`: Full URI for asynchronous PostgreSQL connection (`postgresql+asyncpg`).
-   `REDIS_URI`: Full URI for connecting to Redis.

## 2. Game Session Settings (`app/entities/game_settings.py`)

These settings define the parameters for a specific game session. Some of them have default values defined in the `GameSettings` class, while others can be overridden when creating a game via the `GameCreateSettings` model.

### 2.1. System/Global Game Parameters (usually not changed when creating a game)

These parameters are part of `GameSettings`, but are usually set globally for all games and are not overridden via `GameCreateSettings`.

| Parameter                       | Description                                                      | Default Value (`GameSettings`) |
| :----------------------------- | :------------------------------------------------------------ | :------------------------------------- |
| `cell_size`                    | Cell size on the map in pixels.                            | `40`                                   |
| `default_map_width`            | Default map width (if not loaded from a template).     | `23`                                   |
| `default_map_height`           | Default map height.                                    | `23`                                   |
| `player_default_speed`         | Default player speed.                                 | `3.0`                                  |
| `player_invulnerable_time`     | Player invulnerability time after taking damage (seconds).    | `2.0`                                  |
| `bomb_timer`                   | Time until bomb explosion (seconds).                              | `2.0`                                  |
| `bomb_explosion_duration`      | Duration of bomb explosion display (seconds).              | `0.5`                                  |
| `default_bomb_power`           | Default bomb explosion power (radius).                      | `1`                                    |
| `default_max_bombs`            | Maximum number of bombs that can be placed simultaneously.        | `1`                                    |
| `bullet_speed`                 | Bullet flight speed.                                         | `5.0`                                  |
| `mine_timer`                   | Time until mine explosion after activation (for mines that don't explode immediately). | `1.0` (in `Mine.update`, not `GameSettings.mine_timer` which is `5.0`) |
| `enemy_count_multiplier`       | Enemy count multiplier depending on the level.          | `1.0`                                  |
| `enemy_destroy_animation_time` | Enemy destruction animation time (seconds).                   | `0.5`                                  |
| `enemy_invulnerable_time`      | Enemy invulnerability time after taking damage (seconds).     | `2.0`                                  |
| `block_destroy_score`          | Points for destroying a breakable block.                       | `10`                                   |
| `enemy_destroy_score`          | Points for destroying an enemy.                                    | `100`                                  |
| `powerup_collect_score`        | Points for picking up a power-up.                                      | `25`                                   |
| `level_complete_score`         | Points for completing a level (in Campaign mode).               | `500`                                  |
| `powerup_drop_chance`          | Probability of a power-up dropping from a breakable block.         | `0.2`                                  |
| `enemy_powerup_drop_chance`    | Probability of a power-up dropping from an enemy.                      | `0.3`                                  |
| `enable_snake_walls`           | Use "snake" wall generation for random maps.       | `False`                                |
| `allow_enemies_near_players`   | Allow enemy spawns near players on random maps. | `False`                                |
| `min_distance_from_players`    | Minimum distance (in cells) from players for enemy spawns. | `1`                                    |

### 2.2. Parameters Configurable During Game Creation

These parameters are passed when creating a new game (see NATS event `game.create` and model `app/models/game_create_models.py:GameCreateSettings`). They override the corresponding values in `GameSettings` for a specific session.

| Parameter (`GameCreateSettings`) | Corresponding field in `GameSettings` | Description                                                                 | Default (`GameCreateSettings`) |
| :---------------------------- | :------------------------------------ | :----------------------------------------------------------------------- | :---------------------------------- |
| `game_id`                     | `game_id`                             | Unique game identifier (can be assigned by the server).          | `None`                              |
| `game_mode`                   | `game_mode`                           | Game mode (`campaign`, `free_for_all`, `capture_the_flag`).           | `GameModeType.CAMPAIGN`             |
| `max_players`                 | `max_players`                         | Maximum number of players in the session.                               | `4`                                 |
| `team_count`                  | `team_count`                          | Number of teams (relevant for CTF, FFA determines itself).             | `1`                                 |
| `player_start_lives`          | `player_start_lives`                  | Initial number of lives for players.                                  | `3`                                 |
| `enable_enemies`              | `enable_enemies`                      | Whether to enable enemies on the map.                                             | `True`                              |
| `map_chain_id`                | `map_chain_id`                        | ID of the map chain for sequential progression.                       | `None`                              |
| `map_template_id`             | `map_template_id`                     | ID of the map template for a single game.                                   | `None`                              |
| `respawn_enabled`             | `respawn_enabled`                     | Whether player respawn is enabled after death (depends on mode).           | `False`                             |
| `friendly_fire`               | `friendly_fire`                       | Whether friendly fire is enabled.                               | `False`                             |
| `time_limit`                  | `time_limit`                          | Time limit for the game/round in seconds.                                | `300` (5 minutes)                     |
| `score_limit`                 | `score_limit`                         | Score limit for winning the game/round.                                  | `10`                                |
| `rounds_count`                | `rounds_count`                        | Number of rounds in the game.                                             | `15`                                |

When creating a game via `GameCoordinator` (`game_create`), if a `GameCreateSettings` object is passed, its fields are used to initialize `GameSettings` for that game session. If `GameCreateSettings` is not passed, individual `kwargs` (`game_id`, `game_mode`, `map_template_id`, `map_chain_id`) are used, and other `GameSettings` parameters are taken by default.
