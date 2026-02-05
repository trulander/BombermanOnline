# 3. Deployment and Startup

[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/03_deployment.md)

The service can be run either in a Docker container or locally for development.

## Running with Docker (Recommended)

Building and running the service in Docker is the preferred method for production and staging environments.

1.  **Build the Docker image:**

    From the root directory of the service (`auth-service`), run the command:

    ```bash
    docker build -t auth-service .
    ```

2.  **Run the container:**

    Run the container, exposing port `5003` and passing the necessary environment variables.

    ```bash
    docker run -p 5003:5003 \
      -e POSTGRES_HOST=your_postgres_host \
      -e POSTGRES_USER=your_user \
      -e POSTGRES_PASSWORD=your_password \
      -e SECRET_KEY=your_super_secret_key \
      auth-service
    ```

    For Docker-based startup, secrets are loaded from Infisical. Provide the Infisical access variables and set a service-specific `INFISICAL_PATH`. You can import `services/auth-service/.env-example` into Infisical to create a base configuration.

    Required variables:
    - `INFISICAL_MACHINE_CLIENT_ID`
    - `INFISICAL_MACHINE_CLIENT_SECRET`
    - `INFISICAL_PROJECT_ID`
    - `INFISICAL_SECRET_ENV`
    - `INFISICAL_API_URL`
    - `INFISICAL_PATH`

    > **Note:** For a full list of environment variables, see the [Configuration](./04_configuration.md) section.

## Local Development Setup

For development and debugging, the service can be run locally.

1.  **Install dependencies:**

    It is recommended to use `uv` to create a virtual environment and install packages.

    ```bash
    # Create and activate a virtual environment
    python -m venv .venv
    source .venv/bin/activate

    # Install dependencies
    # Install dependencies from pyproject.toml
    uv pip install -e .
    ```

2.  **Set up environment variables:**

    Create a `.env` file in the project's root directory and specify the necessary variables (see [Configuration](./04_configuration.md)), or run locally with Infisical by providing the `INFISICAL_*` variables.

3.  **Apply migrations:**

    Before the first run, you need to apply migrations to the database.

    ```bash
    alembic upgrade head
    ```

4.  **Run the application:**

    Execute the command from the project's root directory:

    ```bash
    uvicorn app.main:app --host 0.0.0.0 --port 5003 --reload
    ```

    The `--reload` flag will automatically restart the server when code changes.
