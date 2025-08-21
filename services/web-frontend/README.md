# Web Frontend Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

This service represents the user interface for the Bomberman Online game. It provides interaction with the game, including registration and login processes, creating and joining game sessions, and tracking statistics.

## Getting Started

### Local Startup

1.  **Install dependencies**:
    ```bash
    npm install
    ```
2.  **Start the application**:
    ```bash
    npm start
    ```
    The application will be available at `http://localhost:3000`.

### Running with Docker

1.  **Build Docker image**:
    ```bash
    docker build -t bomberman-web-frontend .
    ```
2.  **Run Docker container**:
    ```bash
    docker run -p 3000:3000 bomberman-web-frontend
    ```

## Documentation

More detailed project documentation can be found in the [`docs/`](./docs/) directory:

*   [**User Guide**](./docs/en/user_guide.md): Description of the interface, gameplay, and other features for users.
*   [**Architecture**](./docs/en/architecture.md): Technical description of the application's architecture and its interaction with other services.
*   [**Technology Stack**](./docs/en/tech_stack.md): List of technologies and libraries used.
*   [**Configuration**](./docs/en/configuration.md): Information about settings and environment variables.
*   [**Use Cases**](./docs/en/use_cases.md): Description of user scenarios.
