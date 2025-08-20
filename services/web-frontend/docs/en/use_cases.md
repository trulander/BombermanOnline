# Use Cases (Detailed Overview)
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/use_cases.md)

This document describes the key user interaction scenarios with the system, illustrating them with detailed sequence diagrams.

## 1. Authentication

### UC-1: New User Registration

*   **Description:** A new user creates an account.

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend (React)
    participant AuthService as Auth Service

    User->>Frontend: Opens /account/register
    User->>Frontend: Fills out and submits the form (username, email, password)
    Frontend->>AuthService: POST /users (with form data)
    alt Successful registration
        AuthService->>AuthService: Creates user in DB, sends email
        AuthService-->>Frontend: HTTP 201 Created
        Frontend->>User: Displays success message
    else Error (e.g., email is taken)
        AuthService-->>Frontend: HTTP 4xx/5xx
        Frontend->>User: Displays error message
    end
```

### UC-2: Logging In

*   **Description:** A registered user logs into their account.

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend (React)
    participant AuthService as Auth Service

    User->>Frontend: Opens /account/login, enters credentials
    Frontend->>AuthService: POST /auth/login (username, password)
    AuthService-->>Frontend: { access_token, refresh_token }
    Frontend->>Frontend: tokenService.saveTokens() (in localStorage and `ws_auth_token` cookie)
    Frontend->>AuthService: GET /users/me (with new token)
    AuthService-->>Frontend: { id, username, ... }
    Frontend->>Frontend: Saves user data in AuthContext
    Frontend->>User: Redirects to /account/dashboard
```

## 2. Game Management

### UC-3: Creating and Starting a Game

*   **Description:** A player creates a game, joins it, and starts it.

```mermaid
sequenceDiagram
    participant Player as Player
    participant Frontend as Frontend
    participant WebAPIService as WebAPI Service

    Player->>Frontend: Opens /account/games/create, selects settings
    Frontend->>WebAPIService: POST /games (with settings)
    WebAPIService-->>Frontend: { game_id }
    Frontend->>Player: Redirects to /account/game/{game_id}
    Frontend->>Frontend: In ManageGame, clicks "Join Game"
    Frontend->>WebAPIService: POST /game-service/games/api/v1/players (via proxy)
    WebAPIService-->>Frontend: { success: true }
    Player->>Frontend: Clicks "Start Game"
    Frontend->>WebAPIService: PUT /game-service/games/api/v1/status (action: 'start')
    WebAPIService-->>Frontend: { success: true }
    Frontend->>Player: Updates game status to "Active"
```

### UC-4: Joining a Game from the List

*   **Description:** A player sees a list of games and joins one of them.

```mermaid
sequenceDiagram
    participant Player as Player
    participant Frontend as Frontend
    participant WebAPIService as WebAPI Service
    participant GameService as Game Service

    Player->>Frontend: Opens /account/games
    Frontend->>WebAPIService: GET /games
    WebAPIService-->>Frontend: [ { game_id, status, ... } ]
    Player->>Frontend: Clicks "Join" for game X
    Frontend->>Player: Navigates to /account/game/X
    Frontend->>WebAPIService: Establishes WebSocket connection
    WebAPIService-->>Frontend: Connection established
    Frontend->>WebAPIService: emit('join_game', { game_id: X, player_id: user.id })
    WebAPIService->>GameService: (NATS) join_game
    GameService-->>WebAPIService: (NATS) game_state
    WebAPIService-->>Frontend: emit('game_state', { ... })
    Frontend->>Player: Renders the game board
```

### UC-5: Player Leaves Game

*   **Description:** A player in the lobby decides to leave the game.

```mermaid
sequenceDiagram
    participant Player as Player
    participant Frontend as Frontend
    participant WebAPIService as WebAPI Service

    Player->>Frontend: In the ManageGame window, clicks "Leave Game"
    Frontend->>WebAPIService: DELETE /game-service/games/api/v1/players/{user.id} (via proxy)
    alt Successful deletion
        WebAPIService-->>Frontend: { success: true }
        Frontend->>Frontend: Updates state (isPlayerInThisGame = false)
        Frontend->>Player: Shows the "Join Game" button
    else Error
        WebAPIService-->>Frontend: HTTP 4xx/5xx
        Frontend->>Player: Displays error message
    end
```

## 3. Gameplay

### UC-6: Placing a Bomb

*   **Description:** The player presses the spacebar to place a bomb.

```mermaid
sequenceDiagram
    participant Player as Player
    participant Browser as Browser
    participant InputHandler as InputHandler.ts
    participant GameClient as GameClient.ts
    participant WebAPIService as WebAPI Service

    Player->>Browser: Presses "Spacebar" key
    Browser->>InputHandler: keydown event
    InputHandler->>InputHandler: this.input.weapon1 = true
    GameClient->>InputHandler: In the game loop, calls getInput()
    GameClient->>WebAPIService: emit('place_weapon', { game_id, weapon_action: 'PLACEWEAPON1' })
    InputHandler->>InputHandler: resetWeaponInput() -> this.input.weapon1 = false
```

### UC-7: Automatic Token Refresh In-Game

*   **Description:** The player's `accessToken` expires during the game. The client must refresh it seamlessly without interrupting gameplay.

```mermaid
sequenceDiagram
    participant GameClient as GameClient.ts
    participant SocketIO as Socket.IO
    participant WebAPIService as WebAPI Service
    participant AuthService as Auth Service

    GameClient->>SocketIO: Attempts to send an event (e.g., 'input')
    SocketIO->>WebAPIService: Sends event
    WebAPIService->>WebAPIService: Checks token and finds it has expired
    WebAPIService-->>GameClient: emit('auth_error', { message: 'Token expired' })

    GameClient->>GameClient: Calls handleAuthError()
    GameClient->>AuthService: (via fetch) POST /auth/refresh (with refresh_token)
    AuthService-->>GameClient: { access_token, ... }
    GameClient->>GameClient: tokenService.saveTokens() (updates localStorage and cookie)
    GameClient->>SocketIO: socket.disconnect()
    GameClient->>SocketIO: socket.connect() (with new token in cookie)
```

## 4. Map Editor

### UC-8: Creating and Saving a Map Template

*   **Description:** A user creates a new map template using the interactive editor.

```mermaid
sequenceDiagram
    participant User as User
    participant Frontend as Frontend (MapEditor.tsx)
    participant GameServiceAPI as Game Service API

    User->>Frontend: Clicks "Create New Template"
    Frontend->>User: Opens a dialog with an empty grid
    User->>Frontend: Enters a name, selects "Wall" cell type
    User->>Frontend: "Draws" walls on the grid by holding down the mouse
    Frontend->>Frontend: Updates the local `currentGrid` state on each mouse move
    User->>Frontend: Clicks "Create"
    Frontend->>GameServiceAPI: POST /maps/templates (with name and `grid_data`)
    GameServiceAPI-->>Frontend: { id: "map123", ... }
    Frontend->>Frontend: fetchMapTemplates() to update the list
    Frontend->>User: Closes the dialog and shows the new map in the list
```