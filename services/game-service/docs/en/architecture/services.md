[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../../ru/architecture/services.md)

# Service Layer

The Game Service's service layer contains the core business logic of the application. It is responsible for managing the gameplay, processing events, interacting with data, generating maps, and managing teams.

## 1. `GameCoordinator` (`app/coordinators/game_coordinator.py`)

`GameCoordinator` is the central orchestrator for all active game sessions.

**Main Responsibilities:**

-   **Game Lifecycle Management**: Stores a dictionary of active games (`self.games: dict[str, GameService]`), adds new games upon receiving a `game.create` event, and removes completed games.
-   **NATS Event Handling**: Subscribes to key game NATS events (`game.create`, `game.join`, `game.input`, etc.) via `EventService`. Upon receiving an event, it delegates its processing to the corresponding `GameService` instance or performs the action itself (e.g., creating a new game).
-   **Game Loop (`start_game_loop`)**: Starts an asynchronous loop that, at a specified frequency (`settings.GAME_UPDATE_FPS`):
    -   Iterates through all active games.
    -   Calls the `game.update()` method for each active game.
    -   Sends the updated game state (`updated_state`) to all clients of that game via NATS (`game.update.{game_id}`).
    -   If the game becomes inactive (e.g., finished or no players), it sends a `game.over.{game_id}` event and removes the game from the active list.
-   **Handler Initialization**: In `initialize_handlers()`, it registers callbacks (its own methods) for each NATS event in `EventService`.

**Key NATS Event Handler Methods:**

-   `game_create(**kwargs)`: Creates a new `GameService` instance with the specified settings (`GameCreateSettings` or individual parameters), initializes it (`game_service.initialize_game()`), and adds it to the `self.games` dictionary.
-   `game_join(**kwargs)`: Finds the game by `game_id`, calls `game.add_player()`, and returns the result along with the initial game state.
-   `game_input(**kwargs)`: Finds the game and player, calls `player.set_inputs()`.
-   `game_place_weapon(**kwargs)`: Finds the game and player, calls `game.place_weapon()` with the specified or primary weapon type.
-   `game_get_state(**kwargs)`: Finds the game, calls `game.get_state()`, and adds the full map to it.
-   `game_player_disconnect(**kwargs)`: Finds the game, calls `game.remove_player()`.

## 2. `EventService` (`app/services/event_service.py`)

`EventService` provides an abstraction for working with NATS, simplifying event subscription and publication.

**Main Responsibilities:**

-   **Event Subscription**: The `subscribe_handler(event: NatsEvents, callback: Callable)` method allows subscribing to specific `NatsEvents`. It wraps the provided `callback` (usually a method from `GameCoordinator`) in a `callback_wrapper`, which decodes the incoming message from JSON, calls the `callback`, and if the NATS message had a `reply` field, sends the result back.
-   **Event Publication**: Provides methods for sending typed game events:
    -   `send_game_update(game_id: str, data: dict)`: Sends the `game.update.{game_id}` event.
    -   `send_game_over(game_id: str)`: Sends the `game.over.{game_id}` event.
    -   Uses `NatsRepository` for actual message sending.
-   **Error Handling**: In `callback_wrapper`, it catches exceptions during event processing and sends an error message if `msg.reply` was specified.
-   **Helper Handlers (`handle_...`)**: Contain the logic for calling the passed `callback` for each event type and forming the response.

## 3. `GameService` (`app/services/game_service.py`)

`GameService` encapsulates the logic of a single game session.

**Main Responsibilities:**

-   **Game State Management**: Stores the current game status (`GameStatus`: PENDING, ACTIVE, FINISHED, etc.).
-   **Team Management**: Creates and initializes `TeamService` to manage game teams based on the game mode.
-   **Game Mode**: Upon initialization, creates and stores an instance of a specific game mode (`GameModeService`) that corresponds to the game settings (`self.settings.game_mode`). `TeamService` is passed to the game mode constructor.
-   **Game Initialization (`initialize_game`)**: Sets up default teams via `TeamService` and delegates map initialization to the current game mode (`self.game_mode.initialize_map()`).
-   **Player Management**: Methods `add_player()`, `remove_player()`, `get_player()` delegate calls to the corresponding game mode methods. When a player is added, automatic team distribution is performed.
-   **Game Process Management**: Methods `start_game()`, `pause_game()`, `resume_game()` change the game status. When starting, team setup validity is checked.
-   **State Update (`update`)**: If the game is active, delegates the call to `self.game_mode.update()`. If the mode indicates that the game is over (`self.game_mode.game_over`), it updates the game status to `FINISHED`.
-   **Weapon Application (`place_weapon`)**: Finds the player and delegates weapon application to the game mode.
-   **State Retrieval (`get_state`)**: Retrieves the state from the game mode, adds the overall game status, mode, and team state from `TeamService`.
-   **Activity Check (`is_active`)**: Checks if the game is active and if there are players (delegates to `game_mode.is_active()`).

## 4. `TeamService` (`app/services/team_service.py`)

`TeamService` manages teams within a single game session.

**Main Responsibilities:**

-   **Team Management**: Creation, update, deletion of teams. Stores teams in the `teams: Dict[str, Team]` dictionary.
-   **Player Management in Teams**: Adding and removing players from teams with checks for limits and game mode restrictions.
-   **Automatic Player Distribution**: Implements algorithms for distributing players among teams depending on the game mode:
    -   **CAMPAIGN**: All players in one team.
    -   **FREE_FOR_ALL**: Each player in a separate team.
    -   **CAPTURE_THE_FLAG**: Even distribution among 2-4 teams.
-   **Mode-Specific Settings**: Uses `TeamModeSettings` from `TEAM_MODE_SETTINGS` to define team formation rules.
-   **Team Scoring System**: Awards points to player teams for various game achievements.
-   **Team Validation**: Checks the correctness of team setup before the game starts.

**Key Methods:**

-   `create_team(team_name, team_id=None)`: Creates a new team with limit checks.
-   `add_player_to_team(team_id, player_id)`: Adds a player to a team, removing them from other teams.
-   `remove_player_from_team(team_id, player_id)`: Removes a player from a team.
-   `auto_distribute_players(players, redistribute_existing=False)`: Automatically distributes players among teams according to mode rules.
-   `setup_default_teams()`: Creates default teams for the current game mode.
-   `add_score_to_player_team(player_id, points)`: Awards points to the player's team.
-   `validate_teams()`: Returns a list of team validation errors.
-   `get_teams_state()`: Returns the state of all teams for the API.

## 5. `GameModeService` and its implementations (`app/services/game_mode_service.py`, `app/services/modes/`)

`GameModeService` is an abstract base class that defines the interface for various game modes. Specific modes inherit from it.

**Common to all modes (in `GameModeService`):**

-   State storage: `players`, `enemies`, `weapons`, `power_ups`, `map`, `score`, `level`, `game_over`.
-   **Team Integration**: Accepts `TeamService` in the constructor and uses it for the team scoring system.
-   Map initialization (`initialize_map`): Loads a map from a template/chain via `MapService` or generates a random one, creates enemies.
-   Basic player addition/removal (placement on the map, color assignment). When adding a player, spawn position randomization and player distribution randomization are used depending on the `randomize_spawn_positions` and `randomize_spawn_assignment` settings.
-   State update (`update`): Calculates `delta_time`, updates players, enemies, weapons. Checks if the game is over.
-   Logic for updating individual entities: `update_player`, `update_enemy`, `update_weapon`.
-   Collision handling: `check_collision` (with map and static objects), `check_entity_collision` (between two entities), `check_explosion_collision`.
-   **Team Scoring System**: `handle_player_hit`, `handle_enemy_hit`, `apply_power_up`, `handle_bomb_explosion` now award points to teams via `TeamService` instead of a global score.
-   Weapon mechanics: `place_weapon` (creating bombs, bullets, mines), `handle_bomb_explosion`.
-   Power-up mechanics: `spawn_power_up`, `apply_power_up`.
-   Retrieving full game state for sending to clients (`get_state`).

**Abstract methods (must be implemented in subclasses):**

-   `is_game_over() -> bool`: Checks mode-specific game over conditions.
-   `handle_game_over() -> None`: Actions upon game completion (e.g., determining the winner).
-   `setup_teams() -> None`: Team setup according to mode rules (now delegated to `TeamService`).

**Game Mode Implementations:**

-   **`CampaignMode` (`app/services/modes/campaign_mode.py`)**
    -   Teams are configured via `TeamService` (all players in one team).
    -   The game ends if all players are dead or all enemies on the level are killed.
    -   Upon killing all enemies, the game progresses to the next level (`_level_complete`): level increment, points awarded to the team, map reset, weapons, power-ups, player respawn. When transitioning between levels, players are distributed to spawn points according to randomization settings.
-   **`FreeForAllMode` (`app/services/modes/free_for_all_mode.py`)**
    -   Teams are configured via `TeamService` (each player in their own team).
    -   Enemies are disabled by default (`self.settings.enable_enemies = False`).
    -   The game ends when only one player remains alive or time runs out.
    -   The winner receives points through the team system.
-   **`CaptureFlagMode` (`app/services/modes/capture_flag_mode.py`)**
    -   Teams are configured via `TeamService` (2-4 teams with balanced distribution).
    -   Enemies are disabled.
    -   Flag logic and capture are not fully detailed, but there is a structure for `flag_positions`, `team_flags`, `captured_flags`.
    -   The game ends by team score limit or time limit.
    -   Uses the team scoring system to determine the winner.

## 6. `MapService` (`app/services/map_service.py`)

`MapService` is responsible for all map-related operations.

**Main Responsibilities:**

-   **Creating Maps from Sources**:
    -   `create_map_from_template(template_id)`: Loads a map template from `MapRepository` and creates a `Map` object based on it.
    -   `create_map_from_chain(chain_id, level_index)`: Loads a map chain, selects the required template by level index, and creates a map.
    -   `create_map_from_group(group_id)`: Loads a map group, randomly selects one template, and creates a map.
-   **Generating Random Maps (`generate_random_map`)**:
    -   Creates a `Map` object with specified dimensions.
    -   Adds borders (`_add_border_walls`).
    -   Adds internal walls (in a checkerboard pattern `_add_internal_walls` or "snake" pattern `_add_snake_walls` depending on `game_settings.enable_snake_walls`).
    -   Places player spawn points (`_add_player_spawns`), using the `_generate_spawn_positions` method to generate positions. The method supports various generation strategies:
        -   Using map corners as priority positions (configurable via `use_corner_spawns`)
        -   Generating more spawn points than players (via `spawn_points_count`) for greater randomization
        -   When `randomize_spawn_positions` is enabled, spawn point positions are shuffled before placement on the map
    -   Places breakable blocks (`_add_breakable_blocks`) with a random probability depending on difficulty, avoiding areas near players.
    -   Places enemy spawn points (`_add_enemy_spawns`) on empty cells, considering settings (`allow_enemies_near_players`, `min_distance_from_players`).
-   **Generating Enemies for Level (`generate_enemies_for_level`)**:
    -   Determines the number and types of enemies based on the level number and game settings (`game_settings.enemy_count_multiplier`).
    -   Selects random positions for enemy spawns from those available on the map.

`MapService` closely interacts with `MapRepository` to retrieve data about map templates, groups, and chains, and with `GameSettings` to account for generation parameters.
