# Configuration
[![Русский](https://img.shields.io/badge/lang-Русский-blue.svg)](../ru/configuration.md)

The `web-frontend` service is configured using environment variables. This allows for flexible adaptation of the application for different environments (local development, production). In Docker, secrets can be injected through Infisical.

## Secrets Management (Infisical)

The `.env-example` file contains all available variables and can be imported into Infisical as a base configuration. The Docker entrypoint logs in to Infisical and runs the service with injected environment variables. The required variables are:

- `INFISICAL_MACHINE_CLIENT_ID`
- `INFISICAL_MACHINE_CLIENT_SECRET`
- `INFISICAL_PROJECT_ID`
- `INFISICAL_SECRET_ENV`
- `INFISICAL_API_URL`
- `INFISICAL_PATH`

## Environment Variables

All variables are defined in the `Dockerfile` and can be overridden when starting the Docker container or via a `.env.local` file for local development.

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `NODE_ENV` | Node.js environment mode. Affects build optimization. | `production` |
| `LOGS_ENDPOINT` | Internal endpoint for sending logs to the server. | `/logs` |
| `SERVICE_NAME` | Service name used in logging. | `web-frontend` |
| `SOCKET_URL` | Base URL for connecting to the WebSocket server (`WebAPI Service`). | `http://localhost` |
| `SOCKET_PATH` | Path for the WebSocket connection. | `/socket.io` |
| `LOGS_BATCH_SIZE` | The number of logs that are accumulated before being sent to the server. | `10` |

### Variables for React

Variables with the `REACT_APP_` prefix are embedded into the React application's code during the build phase and are accessible via `process.env`.

| Variable | Description | Default Value |
| :--- | :--- | :--- |
| `REACT_APP_SOCKET_URL` | WebSocket server URL used in the client-side code. | `http://localhost` |
| `REACT_APP_SOCKET_PATH` | Path for the WebSocket connection used in the client-side code. | `/socket.io` |
| `REACT_APP_LOGS_ENDPOINT` | Endpoint for sending logs, used in the client-side code. | `/logs` |
| `REACT_APP_SERVICE_NAME` | Service name used in the client-side code. | `web-frontend` |
| `REACT_APP_LOGS_BATCH_SIZE` | Log batch size used in the client-side code. | `10` |

## Local Development

For local development, you can create a `.env.local` file in the project's root directory and override the necessary variables. Webpack Dev Server will automatically pick them up.

**Example `.env.local`:**

```env
# Redirect requests to the local WebAPI instance
REACT_APP_SOCKET_URL=http://localhost:8080

# Set a more detailed logging level for debugging
REACT_APP_LOG_LEVEL=debug
```