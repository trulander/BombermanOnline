import logging
import time
from pathlib import Path

from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv, VecMonitor

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
        render_freq: int = 500,
        model_name: str | None = None,
    ) -> Path:
        logger.info(
            f"Starting training: total_timesteps={total_timesteps}, "
            f"log_name={log_name}, enable_render={enable_render}, "
            f"render_freq={render_freq}, model_name={model_name}"
        )
        settings.LOGS_PATH.mkdir(parents=True, exist_ok=True)
        settings.MODELS_PATH.mkdir(parents=True, exist_ok=True)
        logger.info(f"Logs path: {settings.LOGS_PATH}, Models path: {settings.MODELS_PATH}")

        render_mode: str | None = "rgb_array" if enable_render else None

        logger.info("Creating BombermanEnv wrapped in DummyVecEnv and VecMonitor")
        # Create vectorized environment
        vec_env = DummyVecEnv(
            env_fns=[
                lambda: BombermanEnv(
                    grpc_client=self.grpc_client,
                    render_mode=render_mode,
                ),
            ],
        )
        # Wrap in VecMonitor to track and log episode metrics (ep_rew_mean, ep_len_mean, etc.)
        env = VecMonitor(vec_env)

        # --- Determine whether to resume from an existing model or create a new one ---
        resume: bool = False
        model_file: Path | None = None

        if model_name is not None:
            # If user passed a name without .zip, append it
            if not model_name.endswith(".zip"):
                model_name = f"{model_name}.zip"
            model_file = settings.MODELS_PATH / model_name

            if model_file.exists():
                logger.info(f"Resuming training from existing model: {model_file}")
                self.model = RecurrentPPO.load(
                    path=model_file,
                    env=env,
                    device="auto",
                    tensorboard_log=str(settings.LOGS_PATH),
                )
                resume = True
            else:
                logger.warning(
                    f"Model file not found at {model_file}, starting fresh training"
                )

        if not resume:
            logger.info("Creating new RecurrentPPO model with MultiInputLstmPolicy")
            self.model = RecurrentPPO(
                policy="MultiInputLstmPolicy",
                env=env,
                verbose=0,
                tensorboard_log=str(settings.LOGS_PATH),
            )

        # --- Callbacks ---
        callbacks = []
        if enable_render:
            logger.info("Render enabled — adding TensorBoardRenderCallback")
            callbacks.append(TensorBoardRenderCallback(render_freq=render_freq))

        # --- Training ---
        # reset_num_timesteps=False keeps the global step counter when resuming,
        # so TensorBoard plots continue seamlessly from the previous run.
        logger.info(f"Starting model.learn for {total_timesteps} timesteps (resume={resume})")
        start_time: float = time.monotonic()
        self.model.learn(
            total_timesteps=total_timesteps,
            tb_log_name=log_name,
            callback=callbacks if callbacks else None,
            reset_num_timesteps=not resume,
        )
        elapsed: float = time.monotonic() - start_time
        logger.info(f"Training completed in {elapsed:.2f}s")

        # --- Save model ---
        # If resuming, overwrite the same file; otherwise save with log_name.
        save_path: Path = model_file if model_file is not None else settings.MODELS_PATH / f"{log_name}.zip"
        self.model.save(path=save_path)
        logger.info(f"Model saved to {save_path}")
        return save_path
