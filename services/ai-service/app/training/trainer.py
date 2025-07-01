import asyncio
import logging
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, Dict, Optional, List, Type

import gymnasium as gym
from stable_baselines3 import PPO, A2C, DQN
from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3.common.callbacks import BaseCallback, CheckpointCallback, EvalCallback
from stable_baselines3.common.env_util import make_vec_env
from stable_baselines3.common.vec_env import DummyVecEnv
from torch.utils.tensorboard import SummaryWriter

from app.environment.bomberman_env import BombermanEnv
from app.repositories.nats_repository import NatsRepository
from app.training.model_manager import ModelManager
from app.config import settings

logger = logging.getLogger(__name__)


class CustomModelSavingCallback(BaseCallback):
    """Callback for saving models at specified intervals."""
    def __init__(self, model_manager: ModelManager, game_mode: str, save_freq: int, verbose: int = 0):
        super().__init__(verbose)
        self.model_manager = model_manager
        self.game_mode = game_mode
        self.save_freq = save_freq
        self.last_saved_timestep = 0

    def _on_step(self) -> bool:
        if (self.num_timesteps - self.last_saved_timestep) >= self.save_freq:
            self.model_manager.save_model(self.model, self.game_mode, self.num_timesteps)
            self.last_saved_timestep = self.num_timesteps
            logger.info(f"Saved model for {self.game_mode} at timestep {self.num_timesteps}")
        return True


class Trainer:
    """Manages the training process for Bomberman AI models."""

    def __init__(self, nats_repository: NatsRepository, model_manager: ModelManager, logs_path: Path = settings.LOGS_PATH):
        self.nats_repository = nats_repository
        self.model_manager = model_manager
        self.logs_path = logs_path
        self.logs_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Trainer initialized. Logs path: {self.logs_path}")



    async def train(self,
                    game_id: str,
                    player_id: str,
                    game_mode: str,
                    total_timesteps: int,
                    save_interval: int,
                    algorithm_name: str = "PPO",
                    learning_rate: float = 0.0003,
                    n_steps: int = 2048,
                    batch_size: int = 64,
                    n_epochs: int = 10,
                    gamma: float = 0.99,
                    gae_lambda: float = 0.95,
                    clip_range: float = 0.2,
                    ent_coef: float = 0.01,
                    verbose: int = 1,
                    continue_training: bool = True,
                    log_interval: int = 10
                    ) -> None:
        new_loop = asyncio.new_event_loop()
        try:
            logger.info(f"Starting training for game {game_id}, player {player_id}, mode {game_mode}")

            def run_loop():
                asyncio.set_event_loop(new_loop)
                new_loop.run_forever()

            with ThreadPoolExecutor() as pool:
                pool.submit(run_loop)

                # Create environment
                # Using a lambda function to pass run-time arguments to the environment
                env = DummyVecEnv([lambda: BombermanEnv(
                    game_id=game_id,
                    player_id=player_id,
                    nats_repository=self.nats_repository,
                    async_loop=new_loop,
                )])

                model = None
                start_timestep = 0
                if continue_training:
                    model = self.model_manager.load_model(game_mode, algorithm_class=self._get_algorithm_class(algorithm_name))
                    if model is not None:
                        # For PPO, the num_timesteps is stored in the model. _last_episode_start_info is not reliable.
                        start_timestep = model.num_timesteps # Assuming SB3 models store this internally
                        logger.info(f"Resuming training from timestep {start_timestep}")

                if model is None:
                    logger.info(f"Creating new {algorithm_name} model for {game_mode}")

                    algorithm_class = self._get_algorithm_class(algorithm_name)
                    common_kwargs = {
                        "policy": "MlpPolicy",
                        "env": env,
                        "learning_rate": learning_rate,
                        "verbose": verbose,
                        "tensorboard_log": str(self.logs_path)
                    }
                    ppo_kwarks = {
                        "clip_range": clip_range
                    }
                    ppo_a2c_kwarks = {
                        "n_steps": n_steps,
                        "batch_size": batch_size,
                        "n_epochs": n_epochs,
                        "gamma": gamma,
                        "gae_lambda": gae_lambda,
                        "ent_coef": ent_coef,
                    }

                    match algorithm_name:
                        case "PPO":
                            common_kwargs.update(**ppo_kwarks)
                            common_kwargs.update(**ppo_a2c_kwarks)
                        case "A2C":
                            common_kwargs.update(**ppo_a2c_kwarks)
                        # case "DQN":

                    model = algorithm_class(
                        **common_kwargs,
                    )
                else:
                    # If loading an existing model, set its environment to the current one
                    model.set_env(env)
                    model.tensorboard_log = str(self.logs_path) # Ensure tensorboard log path is set

                # Callbacks
                callbacks: List[BaseCallback] = [
                    CustomModelSavingCallback(
                        model_manager=self.model_manager,
                        game_mode=game_mode,
                        save_freq=save_interval
                    )
                ]

                # TensorBoard logging will be handled by the model itself via tensorboard_log parameter

                logger.info(f"Training {algorithm_name} model for {game_mode} for {total_timesteps - start_timestep} timesteps...")
                model.learn(total_timesteps=total_timesteps - start_timestep, callback=callbacks, log_interval=log_interval)
                logger.info(f"Training completed for {game_mode}. Final timestep: {model.num_timesteps}")

                # Save final model
                self.model_manager.save_model(model, game_mode, model.num_timesteps)
                logger.info(f"Final model saved for {game_mode} at timestep {model.num_timesteps}")

        except Exception as e:
            logger.error(f"Error during training for game {game_id}, mode {game_mode}: {e}", exc_info=True)

        finally:
            # Останавливаем цикл событий
            new_loop.call_soon_threadsafe(new_loop.stop)


    def _get_algorithm_class(self, algorithm_name: str) -> Type[BaseAlgorithm]:
        if algorithm_name.upper() == "PPO":
            return PPO
        elif algorithm_name.upper() == "A2C":
            return A2C
        elif algorithm_name.upper() == "DQN":
            return DQN
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm_name}")