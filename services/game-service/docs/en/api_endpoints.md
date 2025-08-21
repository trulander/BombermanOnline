[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/api_endpoints.md)

# Game Service API Endpoints

This document describes the HTTP API endpoints provided by the `Game Service`. All endpoints are prefixed with `/games/api/v1`.

## Game Endpoints (`/games`)

*   `GET /games/`
    *   **Description**: Get a list of games with filtering.
    *   **Query Parameters**:
        *   `status` (Optional[GameStatus]): Filter by game status (`PENDING`, `ACTIVE`, `PAUSED`, `FINISHED`).
        *   `game_mode` (Optional[GameModeType]): Filter by game mode (`CAMPAIGN`, `FREE_FOR_ALL`, `CAPTURE_THE_FLAG`).
        *   `has_free_slots` (Optional[bool]): Filter by availability of free slots.
        *   `min_players` (Optional[int]): Minimum number of players.
        *   `max_players` (Optional[int]): Maximum number of players.
        *   `limit` (int): Number of records per page (default 20).
        *   `offset` (int): Offset for pagination (default 0).
    *   **Response**: `List[GameListItem]`
*   `GET /games/{game_id}`
    *   **Description**: Get detailed information about a game by ID.
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
    *   **Response**: `GameInfo`
*   `PUT /games/{game_id}/settings`
    *   **Description**: Update game settings (only for games in `PENDING` status).
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
    *   **Request Body**: `GameSettingsUpdate` (JSON).
    *   **Response**: `StandardResponse`
*   `PUT /games/{game_id}/status`
    *   **Description**: Change game status (`start`/`pause`/`resume`).
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
    *   **Request Body**: `GameStatusUpdate` (JSON).
    *   **Response**: `StandardResponse`
*   `POST /games/{game_id}/players`
    *   **Description**: Add a player to a game.
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
    *   **Request Body**: `PlayerAction` (JSON).
    *   **Response**: `StandardResponse`
*   `DELETE /games/{game_id}/players/{player_id}`
    *   **Description**: Remove a player from a game.
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
        *   `player_id` (str): Unique player identifier.
    *   **Response**: `StandardResponse`
*   `DELETE /games/{game_id}`
    *   **Description**: Delete a game (soft delete).
    *   **Path Parameters**:
        *   `game_id` (str): Unique game identifier.
    *   **Response**: `StandardResponse`

## Entity Endpoints (`/entities`)

*   `GET /entities/info`
    *   **Description**: Get information about available game entities and their types (CellType, GameModeType, GameStatus, EnemyType, PowerUpType, Player units, Weapon types) with their sizes.
    *   **Response**: `Dict[str, Any]`

## Map Endpoints (`/maps`)

*   `POST /maps/templates`
    *   **Description**: Create a new map template.
    *   **Request Body**: `MapTemplateCreate` (JSON).
    *   **Response**: `MapTemplate` (status 201).
*   `GET /maps/templates`
    *   **Description**: Get a list of map templates with filtering.
    *   **Query Parameters**: `name`, `difficulty_min`, `difficulty_max`, `max_players_min`, `max_players_max`, `created_by`, `limit`, `offset`.
    *   **Response**: `List[MapTemplate]`.
*   `GET /maps/templates/{template_id}`
    *   **Description**: Get a map template by ID.
    *   **Path Parameters**: `template_id`.
    *   **Response**: `MapTemplate`.
*   `PUT /maps/templates/{template_id}`
    *   **Description**: Update a map template.
    *   **Path Parameters**: `template_id`.
    *   **Request Body**: `MapTemplateUpdate`.
    *   **Response**: `MapTemplate`.
*   `DELETE /maps/templates/{template_id}`
    *   **Description**: Delete a map template (soft delete).
    *   **Path Parameters**: `template_id`.
    *   **Response**: Status 204.
*   `POST /maps/groups`
    *   **Description**: Create a new map group.
    *   **Request Body**: `MapGroupCreate`.
    *   **Response**: `MapGroup` (status 201).
*   `GET /maps/groups`
    *   **Description**: Get a list of map groups.
    *   **Query Parameters**: `name`, `created_by`, `limit`, `offset`.
    *   **Response**: `List[MapGroup]`.
*   `GET /maps/groups/{group_id}`
    *   **Description**: Get a map group by ID.
    *   **Path Parameters**: `group_id`.
    *   **Response**: `MapGroup`.
*   `PUT /maps/groups/{group_id}`
    *   **Description**: Update a map group.
    *   **Path Parameters**: `group_id`.
    *   **Request Body**: `MapGroupUpdate`.
    *   **Response**: `MapGroup`.
*   `DELETE /maps/groups/{group_id}`
    *   **Description**: Delete a map group (soft delete).
    *   **Path Parameters**: `group_id`.
    *   **Response**: Status 204.
*   `POST /maps/chains`
    *   **Description**: Create a new map chain.
    *   **Request Body**: `MapChainCreate`.
    *   **Response**: `MapChain` (status 201).
*   `GET /maps/chains`
    *   **Description**: Get a list of map chains.
    *   **Query Parameters**: `name`, `created_by`, `limit`, `offset`.
    *   **Response**: `List[MapChain]`.
*   `GET /maps/chains/{chain_id}`
    *   **Description**: Get a map chain by ID.
    *   **Path Parameters**: `chain_id`.
    *   **Response**: `MapChain`.
*   `PUT /maps/chains/{chain_id}`
    *   **Description**: Update a map chain.
    *   **Path Parameters**: `chain_id`.
    *   **Request Body**: `MapChainUpdate`.
    *   **Response**: `MapChain`.
*   `DELETE /maps/chains/{chain_id}`
    *   **Description**: Delete a map chain (soft delete).
    *   **Path Parameters**: `chain_id`.
    *   **Response**: Status 204.

## Team Endpoints (`/teams`)

*   `GET /teams/{game_id}`
    *   **Description**: Get the list of teams for a game.
    *   **Path Parameters**: `game_id`.
    *   **Response**: `List[Team]`.
*   `POST /teams/{game_id}`
    *   **Description**: Create a new team in a game.
    *   **Path Parameters**: `game_id`.
    *   **Request Body**: `TeamCreate`.
    *   **Response**: `Team` (status 201).
*   `PUT /teams/{game_id}/{team_id}`
    *   **Description**: Update a team.
    *   **Path Parameters**: `game_id`, `team_id`.
    *   **Request Body**: `TeamUpdate`.
    *   **Response**: `Team`.
*   `DELETE /teams/{game_id}/{team_id}`
    *   **Description**: Delete a team.
    *   **Path Parameters**: `game_id`, `team_id`.
    *   **Response**: Status 204.
*   `POST /teams/{game_id}/{team_id}/players`
    *   **Description**: Add a player to a team.
    *   **Path Parameters**: `game_id`, `team_id`.
    *   **Request Body**: `PlayerTeamAction`.
    *   **Response**: `Team`.
*   `DELETE /teams/{game_id}/{team_id}/players/{player_id}`
    *   **Description**: Remove a player from a team.
    *   **Path Parameters**: `game_id`, `team_id`, `player_id`.
    *   **Response**: `Team`.
*   `POST /teams/{game_id}/distribute`
    *   **Description**: Automatically distribute players among teams.
    *   **Path Parameters**: `game_id`.
    *   **Request Body**: `TeamDistributionRequest`.
    *   **Response**: `List[Team]`.
*   `GET /teams/{game_id}/validate`
    *   **Description**: Validate the team setup.
    *   **Path Parameters**: `game_id`.
    *   **Response**: `Dict` with validation errors.

## Health Endpoint (`/health`)

*   `GET /health`
    *   **Description**: Check the service status.
    *   **Response**: `Dict` with status information.
