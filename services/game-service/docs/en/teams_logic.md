[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/teams_logic.md)

# Team Logic

This document describes how team logic is implemented in `game-service`, including team creation, player assignment, management via REST API, and specific behavior in various game modes.

## 1. General Overview of Teams

### 1.1. Team System Architecture

The team system in `game-service` is built using a dedicated `TeamService`, which encapsulates all team management logic within a game session:

-   **Teams as Objects**: Each team is represented by a `Team` class with a unique identifier, name, score, and a list of players.
-   **Player Identification**: Each player (`Player`) has a `team_id` attribute (string) that defines their team affiliation.
-   **Centralized Management**: `TeamService` manages all team operations: creation, update, deletion, adding/removing players.
-   **Team Scoring System**: Points are awarded to teams, not individual players, for various game achievements.

### 1.2. Key Components

-   **`Team`** (`app/entities/team.py`): Class representing a team with methods for managing players and score.
-   **`TeamService`** (`app/services/team_service.py`): Service for managing teams in a game session.
-   **`TeamModeSettings`** (`app/entities/team_settings.py`): Team settings for each game mode.
-   **API Models** (`app/models/team_models.py`): Pydantic models for REST API team management.
-   **REST API** (`app/routes/team_routes.py`): HTTP endpoints for team management.

## 2. Team Settings by Game Mode

Each game mode has pre-configured team settings defined in `TEAM_MODE_SETTINGS`:

### 2.1. "Campaign" Mode (CAMPAIGN)

```python
TeamModeSettings(
    default_team_count=1,          # One team
    max_team_count=1,              # Maximum one team
    min_players_per_team=1,        # Minimum 1 player
    max_players_per_team=8,        # Maximum 8 players
    auto_distribute_players=True,   # Automatic distribution
    allow_uneven_teams=True,       # Uneven teams allowed
    default_team_names=["Heroes"]  # Default name
)
```

### 2.2. "Free For All" Mode (FREE_FOR_ALL)

```python
TeamModeSettings(
    default_team_count=0,          # Dynamic number of teams
    max_team_count=8,              # Maximum 8 teams (by number of players)
    min_players_per_team=1,        # Exactly 1 player per team
    max_players_per_team=1,        # Exactly 1 player per team
    auto_distribute_players=True,   # Automatic distribution
    allow_uneven_teams=True,       # Uneven teams allowed
    default_team_names=[]          # Names are generated automatically
)
```

### 2.3. "Capture The Flag" Mode (CAPTURE_THE_FLAG)

```python
TeamModeSettings(
    default_team_count=2,          # Two teams
    max_team_count=4,              # Maximum 4 teams
    min_players_per_team=1,        # Minimum 1 player
    max_players_per_team=4,        # Maximum 4 players
    auto_distribute_players=True,   # Automatic distribution
    allow_uneven_teams=False,      # Teams must be even
    default_team_names=["Red Team", "Blue Team", "Green Team", "Yellow Team"]
)
```

## 3. Team Lifecycle

### 3.1. Team Initialization

When a game is created:

1.  **TeamService Creation**: `GameService` creates a `TeamService` instance for the current game mode.
2.  **Default Team Setup**: `team_service.setup_default_teams()` is called, which creates teams according to the mode settings.
3.  **Pass to Game Mode**: `TeamService` is passed to the `GameModeService` constructor.

### 3.2. Adding Players

When adding a player to a game:

1.  **Add to Game Mode**: The player is added via `game_mode.add_player()`.
2.  **Automatic Distribution**: `team_service.auto_distribute_players()` is called to assign the player to a team.
3.  **Update team_id**: The player's `team_id` is set.

### 3.3. Distribution Algorithms

#### "Campaign" Mode
All players are added to a single "Heroes" team.

#### "Free For All" Mode
For each player, an individual team is created with the name "{PlayerName}'s Team".

#### "Capture The Flag" Mode
Players are evenly distributed among teams using a round-robin algorithm to ensure balance.

## 4. Team Scoring System

### 4.1. Score Sources

Teams receive points for the following actions:

-   **Destroying blocks**: `settings.block_destroy_score` points for destroying a block with a bomb.
-   **Killing enemies**: `settings.enemy_destroy_score` points for destroying an enemy.
-   **Collecting power-ups**: `settings.powerup_collect_score` points for picking up a power-up.
-   **Completing a level**: `settings.level_complete_score` points for completing a level (campaign mode).
-   **Winning a round**: Winner's points in "Free For All" mode.

### 4.2. Awarding Points

Points are awarded via the `team_service.add_score_to_player_team(player_id, points)` method, which:

1.  Finds the player's team.
2.  Adds the specified number of points to the team's score.
3.  Updates the team's state.

## 5. REST API for Team Management

### 5.1. Available Operations

The system provides a full REST API for team management:

-   **`GET /teams/{game_id}`**: Get a list of game teams.
-   **`POST /teams/{game_id}`**: Create a new team.
-   **`PUT /teams/{game_id}/{team_id}`**: Update a team.
-   **`DELETE /teams/{game_id}/{team_id}`**: Delete a team.
-   **`POST /teams/{game_id}/{team_id}/players`**: Add a player to a team.
-   **`DELETE /teams/{game_id}/{team_id}/players/{player_id}`**: Remove a player from a team.
-   **`POST /teams/{game_id}/distribute`**: Automatically distribute players.
-   **`GET /teams/{game_id}/validate`**: Validate team setup.

### 5.2. Limitations

-   All team operations are only available for games in `PENDING` status.
-   Limits on the number of teams and players per team are observed according to mode settings.
-   Player existence in the game is checked before adding to a team.

## 6. Integration with Game Modes

### 6.1. Updated Architecture

Game modes no longer manage teams directly. Instead:

1.  **Constructor receives TeamService**: `GameModeService` accepts `TeamService` in its constructor.
2.  **Delegation of Operations**: `setup_teams()` methods in modes now simply log the completion of setup.
3.  **Using Team Scores**: All score awarding operations use `TeamService`.

### 6.2. Mode Specifics

#### CampaignMode
-   Uses a single team for all players.
-   Upon level completion, points are awarded to the team via the first player.
-   Teamwork and cooperation.

#### FreeForAllMode
-   Each player has an individual team.
-   The winner receives bonus points.
-   Competitive nature of the game.

#### CaptureFlagMode
-   Uses balanced teams.
-   Points are awarded for team achievements.
-   Strategic team play.

## 7. Validation and Checks

### 7.1. Automatic Validation

`TeamService` provides a `validate_teams()` method that checks:

-   Compliance with the minimum number of players per team.
-   Team size equality (if required by mode settings).
-   Compliance with game mode restrictions.

### 7.2. Checks on Launch

When a game is launched (`game_service.start_game()`), team validation is performed. Validation errors are logged but do not block the launch (only warn).

## 8. Game State and Teams

### 8.1. Inclusion in State

Team information is included in the game state via `game_service.get_state()`:

```json
{
  "teams": {
    "team_id_1": {
      "id": "team_id_1",
      "name": "Red Team",
      "score": 150,
      "player_ids": ["player_1", "player_2"],
      "player_count": 2
    }
  }
}
```

### 8.2. State Updates

Team state is automatically updated when:
-   Players are added/removed from a team.
-   Points are awarded to a team.
-   Team name is changed.

## 9. Migration and Compatibility

### 9.1. Backward Compatibility


### 9.2. Transition from Old System

The old system with a team dictionary in `GameModeService` has been completely replaced by `TeamService`, providing:
-   Clearer separation of responsibilities.
-   Centralized team management.
-   Extended capabilities via REST API.
-   Flexible settings for different game modes.

This system provides full, flexible, and extensible functionality for managing teams in all supported game modes.
