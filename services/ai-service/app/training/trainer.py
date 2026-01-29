from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

from app.ai_env.bomberman_env import BombermanEnv
from app.config import settings
from app.services.grpc_client import GameServiceGRPCClient


class TrainingService:
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
    ) -> None:
        self.grpc_client = grpc_client
        self.model: PPO | None = None

    def start_training(
        self,
        total_timesteps: int = 1000,
        log_name: str = "bomberman_ai",
    ) -> Path:
        settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)

        env = DummyVecEnv(
            env_fns=[lambda: BombermanEnv(grpc_client=self.grpc_client)],
        )
        self.model = PPO(
            policy="MlpPolicy",
            env=env,
            verbose=1,
            tensorboard_log=str(settings.LOGS_PATH),
        )
        self.model.learn(
            total_timesteps=total_timesteps,
            tb_log_name=log_name,
        )

        model_path = settings.MODELS_PATH / f"{log_name}.zip"
        self.model.save(
            path=model_path,
        )
        return model_path