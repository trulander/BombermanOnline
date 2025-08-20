# Web Frontend Service
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](README_RU.md)

This service is the user interface for the Bomberman Online game. It handles interaction with the game, including registration and login processes, creating and joining game sessions, and tracking statistics.

## Getting Started

### Local Launch

1.  **Install dependencies**:
    ```bash
    npm install
    ```
2.  **Run the application**:
    ```bash
    npm start
    ```
    The application will be available at `http://localhost:3000`.

### Running with Docker

1.  **Build the Docker image**:
    ```bash
    docker build -t bomberman-web-frontend .
    ```
2.  **Run the Docker container**:
    ```bash
    docker run -p 3000:3000 bomberman-web-frontend
    ```

## Documentation

More detailed project documentation can be found in the [`docs/`](./docs/) directory:

*   [**User Guide**](./docs/en/user_guide.md): Description of the interface, gameplay, and other features for users.
*   [**Architecture**](./docs/en/architecture.md): Technical description of the application architecture and its interaction with other services.
*   [**Technology Stack**](./docs/en/tech_stack.md): A list of technologies and libraries used.
*   [**Configuration**](./docs/en/configuration.md): Information about settings and environment variables.
*   [**Use Cases**](./docs/en/use_cases.md): Description of user scenarios.