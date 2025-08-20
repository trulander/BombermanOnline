# AI Service
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](README_RU.md)

The AI Service is a component of the Bomberman Online platform responsible for managing AI units (enemies and bot players) in game sessions, as well as for training artificial intelligence models.

## Service Purpose

The service simulates the behavior of AI-controlled entities in the game world. It receives the game state from `game-service`, makes decisions based on loaded models, and sends control commands back via NATS.

## Technologies Used

*   **Python 3.12**
*   **FastAPI** & **Uvicorn**
*   **NATS (`nats-py`)** for asynchronous interaction
*   **Redis (`redis-py`)** for caching
*   **Gymnasium**, **Stable-Baselines3**, **TensorBoard** for model training
*   **Pydantic** for validation and configuration
*   **Numpy** for data manipulation
*   **`uv`** for dependency management

## Documentation

All detailed documentation for the service is divided into the following sections:

*   **[Project Structure](docs/en/project_structure.md)**: Description of files and directories.
*   **[Dependencies and Technologies](docs/en/packages.md)**: A detailed overview of the libraries used.
*   **[Deployment and Startup](docs/en/deployment.md)**: Instructions for local startup and Docker usage.
*   **[Interaction and Use Cases](docs/en/interaction.md)**: Description of the NATS API, diagrams, and usage scenarios.
*   **[AI Model Training](docs/en/ai_training.md)**: Details of the reinforcement learning process.
*   **[Configuration](docs/en/configuration.md)**: A complete list of environment variables.
