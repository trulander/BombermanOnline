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

## Training and Inference Skeleton

-   Training and inference are triggered via gRPC, no HTTP training endpoint is used.
-   Gymnasium `BombermanEnv` proxies `reset/step` to the gRPC client for `game-service` in training mode.
-   Stable-Baselines3 saves models to `MODELS_PATH`, TensorBoard logs are written to `LOGS_PATH` and read by `tensorboard` in `infra/docker-compose.yml`.

## gRPC Training

-   `Reset` creates a training session in `game-service` and returns `session_id` and observation.
-   `Step` accepts `action` and `delta_seconds` (default 0.33 sec) and returns observation, `reward`, `terminated`, `truncated`.
-   Observation is a `15x15` map window (225 values) + 6 scalars: `x_norm`, `y_norm`, `lives_norm`, `enemy_norm`, `map_width_norm`, `map_height_norm`.
-   Actions: `0` — no-op, `1` — up, `2` — down, `3` — left, `4` — right, `5` — place_weapon_1.

## Postman

Файлы для импорта в Postman находятся в `services/ai-service/postman`:

- `ai-service-rest.postman_collection.json` — REST эндпоинты
- `ai-service.postman_environment.json` — окружение


## Documentation

All detailed service documentation is divided into the following sections:

*   **[Project Structure](docs/en/project_structure.md)**: Description of files and directories.
*   **[Dependencies and Technologies](docs/en/packages.md)**: Detailed overview of libraries used.
*   **[Deployment and Startup](docs/en/deployment.md)**: Instructions for local startup and Docker usage.
*   **[Interaction and Use Cases](docs/en/interaction.md)**: Description of NATS API, diagrams, and use cases.
*   **[AI Model Training](docs/en/ai_training.md)**: Details of the reinforcement learning process.
*   **[Configuration](docs/en/configuration.md)**: Full list of environment variables.
*   **[Training and Inference Flow](docs/ru/examples/ai_service_flow.md)**: Interaction diagram.
*   **[Training Flow](docs/ru/examples/ai_training_flow.md)**: gRPC training diagram.

## Secrets Management

Secrets are managed in Infisical. The `.env-example` file contains all available variables and can be imported into Infisical as a base configuration. The Docker entrypoint logs in to Infisical and runs the service with injected environment variables.

## Testing

From `services/ai-service`:

```bash
uv pip install .
uv run pytest
```