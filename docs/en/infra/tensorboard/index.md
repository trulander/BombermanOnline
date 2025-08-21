# TensorBoard
[![Russian](https://img.shields.io/badge/lang-Russian-blue.svg)](../../../ru/infra/tensorboard/index.md)

## Purpose in the Project

**TensorBoard** is a visualization toolkit from the TensorFlow ecosystem. In this project, it is used to **visualize the AI model training process**.

The `ai-service` saves training logs (e.g., loss function values, accuracy, gradients) in a special format during model training. TensorBoard reads these logs and presents them as interactive graphs and dashboards.

This allows for:
-   Tracking training progress in real-time.
-   Analyzing and comparing different model runs.
-   Debugging the neural network architecture and hyperparameters.

## Configuration

The `tensorboard` service is defined in `infra/docker-compose.yml`:

```yaml
services:
  tensorboard:
    image: tensorflow/tensorboard:latest
    volumes:
      - ../infra/ai_logs:/tf/logs
    ports:
      - "6006:6006"
    command: tensorboard --logdir=/tf/logs --host 0.0.0.0 --port 6006
```

-   **`image`**: `tensorflow/tensorboard:latest` - the official image.
-   **`volumes`**: The `infra/ai_logs` directory from the host, where `ai-service` saves logs, is mounted into the container at `/tf/logs`.
-   **`ports`**: `6006:6006` - the standard port for accessing the TensorBoard web UI.
-   **`command`**: Starts TensorBoard and tells it to read logs from the `/tf/logs` directory.

## Access

-   **TensorBoard Web UI**: `http://localhost:6006`
-   The service is not routed through Traefik.
