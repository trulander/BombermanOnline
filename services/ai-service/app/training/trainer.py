import logging
import time
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from app.ai_env.bomberman_env import BombermanEnv
from app.config import settings
from app.services.grpc_client import GameServiceGRPCClient

logger = logging.getLogger(__name__)


class TrainingService:
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
    ) -> None:
        self.grpc_client = grpc_client
        self.model: PPO | None = None
        logger.info("TrainingService initialized")

    def start_training(
        self,
        total_timesteps: int = 1000,
        log_name: str = "bomberman_ai",
    ) -> Path:
        logger.info(f"Starting training: total_timesteps={total_timesteps}, log_name={log_name}")
        settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Logs path: {settings.LOGS_PATH}, Models path: {settings.MODELS_PATH}")

        logger.info("Creating BombermanEnv wrapped in DummyVecEnv")
        env = DummyVecEnv(
            env_fns=[lambda: BombermanEnv(grpc_client=self.grpc_client)],
        )

        logger.info("Creating PPO model with MlpPolicy")
        self.model = PPO(
            policy="MlpPolicy",
            env=env,
            verbose=1,
            tensorboard_log=str(settings.LOGS_PATH),
        )

        logger.info(f"Starting model.learn for {total_timesteps} timesteps")
        start_time: float = time.monotonic()
        self.model.learn(
            total_timesteps=total_timesteps,
            tb_log_name=log_name,
        )
        elapsed: float = time.monotonic() - start_time
        logger.info(f"Training completed in {elapsed:.2f}s")

        model_path = settings.MODELS_PATH / f"{log_name}.zip"
        self.model.save(
            path=model_path,
        )
        logger.info(f"Model saved to {model_path}")
        return model_path