import logging
import time
from pathlib import Path

from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv

from app.ai_env.bomberman_env import BombermanEnv
from app.config import settings
from app.services.grpc_client import GameServiceGRPCClient
from app.training.render_callback import TensorBoardRenderCallback

logger = logging.getLogger(__name__)


class TrainingService:
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
    ) -> None:
        self.grpc_client = grpc_client
        self.model: RecurrentPPO | None = None
        logger.info("TrainingService initialized")

    def start_training(
        self,
        total_timesteps: int = 1000,
        log_name: str = "bomberman_ai",
        enable_render: bool = False,
        render_freq: int = 500
    ) -> Path:
        logger.info(
            f"Starting training: total_timesteps={total_timesteps}, "
            f"log_name={log_name}, enable_render={enable_render}"
            f"render_freq={render_freq}"
        )
        settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Logs path: {settings.LOGS_PATH}, Models path: {settings.MODELS_PATH}")

        render_mode: str | None = "rgb_array" if enable_render else None

        logger.info("Creating BombermanEnv wrapped in DummyVecEnv")
        env = DummyVecEnv(
            env_fns=[
                lambda: BombermanEnv(
                    grpc_client=self.grpc_client,
                    render_mode=render_mode,
                ),
            ],
        )

        logger.info("Creating RecurrentPPO model with MultiInputLstmPolicy")
        self.model = RecurrentPPO(
            policy="MultiInputLstmPolicy",
            env=env,
            verbose=1,
            tensorboard_log=str(settings.LOGS_PATH),
        )

        callbacks = []
        if enable_render:
            logger.info("Render enabled — adding TensorBoardRenderCallback")
            callbacks.append(TensorBoardRenderCallback(render_freq=render_freq))

        logger.info(f"Starting model.learn for {total_timesteps} timesteps")
        start_time: float = time.monotonic()
        self.model.learn(
            total_timesteps=total_timesteps,
            tb_log_name=log_name,
            callback=callbacks if callbacks else None,
        )
        elapsed: float = time.monotonic() - start_time
        logger.info(f"Training completed in {elapsed:.2f}s")

        model_path = settings.MODELS_PATH / f"{log_name}.zip"
        self.model.save(
            path=model_path,
        )
        logger.info(f"Model saved to {model_path}")
        return model_path
