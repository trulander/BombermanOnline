# Deployment and Running
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/deployment.md)

This section contains instructions for running the `WebAPI Service` for development and in a production environment.

## Local Development Run

This method is recommended for development and debugging.

### Requirements
*   Python 3.12+
*   [uv](https://github.com/astral-sh/uv) for dependency management.
*   Available instances of **Redis** and **NATS**.

### Steps

1.  **Clone the repository** (if you haven\'t already):
```bash
git clone <your-repo-url>
cd services/webapi-service
```

2.  **Install dependencies**:
*   `uv` will create a virtual environment and install packages from `pyproject.toml` into it.
```bash
uv sync
```

3.  **Configure environment variables**:
*   Copy the `.env-example` file to `.env`:
```bash
cp .env-example .env
```
*   Edit `.env`, specifying the correct addresses for `REDIS_HOST`, `NATS_URL`, and `CONSUL_HOST`.

4.  **Start the server**:
*   `uv` will run Uvicorn in the context of the created virtual environment.
```bash
uv run uvicorn webapi-service.app.main:app --host 0.0.0.0 --port 5001 --reload
```

5.  **Verification**:
*   Open `http://localhost:5001` in your browser. You should see a welcome page.
*   The Swagger UI documentation will be available at `http://localhost:5001/webapi/docs` (or at the URL specified in `SWAGGER_URL`).

## Running with Docker

This method is suitable for creating an isolated environment and preparing for production deployment.

### Requirements
*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/) (recommended for managing multiple services)

### Building the Docker Image

From the `services/webapi-service` directory, run the command:

```bash
docker build -t bomberman-webapi-service .
```

### Running the Docker Container

You can run the service in a container, passing all necessary environment variables via the `-e` flag.

```bash
docker run -p 5001:5001 \
    -e NATS_URL=nats://<nats_host>:4222 \
    -e REDIS_HOST=<redis_host> \
    -e CONSUL_HOST=<consul_host> \
    --name webapi_service \
    bomberman-webapi-service
```

*   Replace `<nats_host>`, `<redis_host>`, and `<consul_host>` with the actual addresses of your dependencies. If they are running on the same machine, you can use `host.docker.internal`.

### Using Docker Compose (Recommended Method)

For a comprehensive deployment of the entire system (including `WebAPI`, `Game Service`, `NATS`, `Redis`, etc.), it is recommended to use the `docker-compose.yml` from the project\'s root directory.

1.  **Configure `docker-compose.yml`**:
*   Ensure that the `webapi-service` is defined in the `docker-compose.yml` file.
*   Check that all environment variables for the service are set correctly in the `environment` section.

2.  **Start all services**:
*   This command will build the images (if necessary) and start all services in the background.
```bash
docker-compose up -d
```

3.  **View logs**:
*   To view the logs of a specific service, use:
```bash
docker-compose logs -f webapi-service
```

4.  **Stopping**:
*   To stop all running services:
```bash
docker-compose down
```
