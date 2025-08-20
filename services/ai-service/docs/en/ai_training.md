# AI Model Training
[![Russian](https://img.shields.io/badge/lang-Russian-blue)](../ru/ai_training.md)

## Concept

The service uses Reinforcement Learning to create AI behavior models. The training process takes place in a custom environment that simulates the rules and mechanics of the game Bomberman.

## Training Environment (`BombermanEnv`)

*   **Base**: `gymnasium.Env`
*   **Purpose**: Provides a standardized interface for interacting with the RL agent.
*   **Key Components**:
    *   **State**: A representation of the game world in a format understandable to the model (usually a multi-dimensional `numpy` array). It includes the positions of walls, players, enemies, bombs, and bonuses.
    *   **Action Space**: The set of all possible actions an agent can take (move up/down/left/right, place a bomb, do nothing).
    *   **Reward**: A numerical score the agent receives for its actions. A well-configured reward function is key to training effective behavior.
        *   *Positive reward*: for destroying an enemy, collecting a bonus, surviving.
        *   *Negative reward (penalty)*: for death, loss of health points, inaction.
    *   **`step()` method**: Takes an action from the agent, updates the environment's state, and returns the new state, reward, and a flag indicating the end of the episode.
    *   **`reset()` method**: Resets the environment to its initial state to start a new training episode.

## Training Process (`Trainer`)

1.  **Initialization**: An instance of the `BombermanEnv` environment and a model from `Stable-Baselines3` (e.g., `PPO`) are created.
2.  **Training**: The `model.learn()` method is launched, which iterates through episodes:
    *   The agent performs actions in the environment.
    *   The environment returns the result (new state, reward).
    *   The agent uses this information to update its internal policy (neural network) to choose more "advantageous" actions in the future.
3.  **Logging**: Training metrics (average reward, episode length, etc.) are automatically logged. These logs can be viewed using TensorBoard.
4.  **Saving**: Periodically (e.g., every N steps), the trained model is saved to a file using `ModelManager`.

## Model Management (`ModelManager`)

*   **Saving**: Saves the trained model to the directory specified in `MODELS_PATH` (`/app/ai_models` in the container). The filename usually includes the model name and the number of training steps, e.g., `ppo_bomberman_1000000_steps.zip`.
*   **Loading**: On service startup or by command, `ModelManager` can load a previously saved model to use it for managing units in the game (inference).

## Monitoring with TensorBoard

Logs for TensorBoard are saved to the directory specified in `LOGS_PATH` (`/app/ai_logs` in the container).

To view the training progress:
1.  Ensure that the log directory (`infra/ai_logs` on the host) is mapped to the container or is accessible locally.
2.  Launch TensorBoard:
    ```bash
    tensorboard --logdir=./infra/ai_logs --host 0.0.0.0 --port 6006
    ```
3.  Open `http://localhost:6006` in your browser.
