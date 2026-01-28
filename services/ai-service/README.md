# AI Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

AI Service is a component of the Bomberman Online platform responsible for managing AI units (enemies and bot players) in game sessions, as well as training artificial intelligence models.

## Service Purpose

The service simulates the behavior of AI-controlled entities in the game world. It receives the game state from `game-service`, makes decisions based on loaded models, and sends control commands back via gRPC.

## Technologies Used

*   **Python 3.12**
*   **FastAPI** & **Uvicorn**
*   **gRPC** for synchronous interaction
*   **NATS (`nats-py`)** for asynchronous interaction for require game-service instances from game-allocation-service
*   **Redis (`redis-py`)** for caching
*   **Gymnasium**, **Stable-Baselines3**, **TensorBoard** for model training
*   **Pydantic** for validation and configuration
*   **Numpy** for data manipulation
*   **`uv`** for dependency management

## Documentation

All detailed service documentation is divided into the following sections:

*   **[Project Structure](docs/en/project_structure.md)**: Description of files and directories.
*   **[Dependencies and Technologies](docs/en/packages.md)**: Detailed overview of libraries used.
*   **[Deployment and Startup](docs/en/deployment.md)**: Instructions for local startup and Docker usage.
*   **[Interaction and Use Cases](docs/en/interaction.md)**: Description of NATS API, diagrams, and use cases.
*   **[AI Model Training](docs/en/ai_training.md)**: Details of the reinforcement learning process.
*   **[Configuration](docs/en/configuration.md)**: Full list of environment variables.