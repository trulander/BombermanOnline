# Dependencies and Technologies
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/packages.md)

## Core Stack

*   **Python 3.12**: The primary programming language.
*   **FastAPI**: A web framework for creating APIs. Although the main interaction is via NATS, FastAPI is used for potential HTTP endpoints (e.g., health checks).
*   **Uvicorn**: An ASGI server for running FastAPI.
*   **Pydantic**: For data validation, especially for configuration settings and data models received from NATS.

## Interaction and Network

*   **NATS (`nats-py`)**: The primary transport for asynchronous messaging with `game-service`.
*   **Redis (`redis-py`)**: Used for caching and storing temporary data, such as states or model metadata.
*   **Consul (`py-consul`)**: For service registration and discovery of other services in the ecosystem.

## Machine Learning

*   **Gymnasium**: A fork of OpenAI Gym, providing a standardized API for creating and working with Reinforcement Learning environments.
*   **Stable-Baselines3**: A library with implementations of modern RL algorithms (PPO, A2C, DQN, etc.).
*   **TensorFlow/PyTorch**: Stable-Baselines3 uses one of these libraries as its backend. Dependencies are pulled in automatically.
*   **TensorBoard**: A tool for visualizing model training metrics.
*   **Numpy**: The foundation for all numerical operations, especially when processing game states and rewards.

## Utilities

*   **`python-json-logger`**: For outputting logs in a structured JSON format.
*   **`uv`**: A modern and fast package manager used for installing and synchronizing dependencies.
