# Deployment and Startup
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/deployment.md)

## Local Startup (for development)

This method is suitable for local development and debugging.

1.  **Install Dependencies**:
    Make sure you have `uv` installed. Then, in the `services/ai-service` directory, run:
    ```bash
    uv sync
    ```

2.  **Start the Application**:
    To start the service, running instances of NATS and Redis must be available.
    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 5004 --reload
    ```
    The `--reload` flag automatically restarts the service when the code changes.

## Running with Docker

This is the recommended method for integration and deployment.

### Building the Image

From the root directory of the service (`services/ai-service`), run the command:
```bash
docker build -t bomberman-ai-service .
```

### Dockerfile Analysis

```dockerfile
# Use the official Python 3.12 image
FROM python:3.12-slim-bookworm

# Set the working directory inside the container
WORKDIR /app

# Install uv for dependency management
RUN pip install uv

# Copy the dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies using uv
RUN uv sync

# Copy the application source code
COPY app ./app

# Default command to run the FastAPI application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "5004"]
```

### Running the Container

To fully run the service in Docker, it needs to be integrated into the project's overall `docker-compose.yml` infrastructure to ensure interaction with other services like `game-service`, `NATS`, and `Redis`.

Example command for manually running the container:
```bash
docker run -p 5004:5004 \
       --network=bomberman-network \
       --env-file .env \
       -v ./infra/ai_models:/app/ai_models \
       -v ./infra/ai_logs:/app/ai_logs \
       bomberman-ai-service
```
*   `--network`: Connects the container to the same Docker network as the other services.
*   `--env-file`: Passes environment variables from the `.env` file.
*   `-v`: Mounts the local directories `infra/ai_models` and `infra/ai_logs` inside the container to save models and training logs.

```