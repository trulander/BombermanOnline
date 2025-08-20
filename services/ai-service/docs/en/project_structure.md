# Project Structure
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/project_structure.md)

Below is the structure of the service's directories and files with a description of their purpose.

```
services/ai-service/
├── app/
│   ├── __init__.py
│   ├── main.py                   # Entry point for the FastAPI application, service initialization.
│   ├── config.py                 # Configuration settings managed by environment variables.
│   ├── nats_controller.py        # Logic for processing messages from NATS (subscriptions and publications).
│   ├── agents/                   # Implementations of AI agents.
│   │   ├── base_agent.py         # Abstract base class for all agents.
│   │   ├── bomberman_ai_agent.py # Agent that controls an AI player.
│   │   └── enemy_ai_agent.py     # Agent that controls enemies.
│   ├── entities/                 # Pydantic models for data representation.
│   │   └── game_state_representation.py # Model for deserializing the game state.
│   ├── environment/              # Gymnasium environment for AI training.
│   │   └── bomberman_env.py      # Custom training environment simulating the Bomberman game.
│   ├── registry/                 # Registries for managing in-memory objects.
│   │   └── ai_agent_registry.py  # Registry for storing and managing active AI agents.
│   ├── repositories/             # Repositories for interacting with external systems.
│   │   ├── nats_repository.py    # Abstraction for working with NATS.
│   │   └── redis_repository.py   # Abstraction for working with Redis.
│   └── training/                 # Logic for model training.
│       ├── model_manager.py      # Manages saving and loading models.
│       └── trainer.py            # Orchestrator for the model training process.
├── Dockerfile                    # Definition of the Docker image for the service.
├── pyproject.toml                # Definition of dependencies and project configuration.
├── README.md                     # Documentation in English.
└── README_RU.md                  # Main documentation file in Russian.
```
