[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/introduction.md)

# Introduction to Game Service

Game Service is the heart of the Bomberman online platform. It is responsible for all core game logic, from match creation to managing real-time player interactions.

## Key Functions

-   **Game Session Management**: Creation, configuration, and termination of game sessions.
-   **Game Mode Support**:
    -   `Campaign`: Cooperative or single-player level progression.
    -   `Free For All`: Every player for themselves.
    -   `Capture The Flag`: Team-based game with flag capture (planned, basic structure exists).
-   **Player Management**: Adding, removing, tracking state (lives, power-ups, position), processing command input.
-   **Game Mechanics**:
    -   Placing and exploding bombs.
    -   Using other weapons (bullets, mines).
    -   Interacting with breakable blocks.
    -   Picking up and applying power-ups.
-   **Map Management**:
    -   Generating random maps with various parameters.
    -   Loading maps from predefined templates.
    -   Supporting map chains for sequential progression (e.g., in campaign).
-   **Artificial Intelligence (AI)**: Basic management of enemy behavior on the map.
-   **Event-driven Model**: Interaction with other services and clients via NATS for real-time game state updates and command processing.
-   **REST API**: Providing an API for managing map-related resources (templates, groups, chains).
-   **Persistence and Caching**: Storing map template data in PostgreSQL and caching it in Redis for fast access.

## Interaction within the Ecosystem

Game Service is tightly integrated with other components of the platform:

-   **WebAPI Service**: Through it, users can initiate game creation, view available games, etc. (presumably).
-   **Auth Service**: For player authentication and authorization (via middleware, receiving user data from headers).
-   **NATS**: As a message bus for game events, player commands, and game state updates.
-   **Client Applications**: Receive game state updates and send player commands via NATS.

This service is designed to be scalable and fault-tolerant, ensuring a smooth and engaging gameplay experience.
