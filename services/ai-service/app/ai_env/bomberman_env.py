import logging

import numpy as np
import gymnasium as gym
from gymnasium import spaces

from app.services.grpc_client import GameServiceGRPCClient

logger = logging.getLogger(__name__)


class BombermanEnv(gym.Env[np.ndarray, int]):
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
        obs_shape: tuple[int, ...] = (231,),
        action_count: int = 6,
    ) -> None:
        self.grpc_client = grpc_client
        self.action_space = spaces.Discrete(n=action_count)
        self.observation_space = spaces.Box(
            low=0.0,
            high=1.0,
            shape=obs_shape,
            dtype=np.float32,
        )
        self.session_id: str | None = None
        self._last_obs = np.zeros(obs_shape, dtype=np.float32)
        self._step_count: int = 0
        logger.info(f"BombermanEnv initialized: obs_shape={obs_shape}, action_count={action_count}")

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        logger.info(f"BombermanEnv.reset called: seed={seed}, options={options}")
        self._step_count = 0
        observation, info, session_id = self.grpc_client.reset(options=options)
        if observation is None:
            logger.warning("BombermanEnv.reset: received None observation, using zeros")
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)
        self.session_id = session_id
        self._last_obs = observation
        logger.info(f"BombermanEnv.reset completed: session_id={session_id}, obs_shape={observation.shape}")
        return observation, info or {}

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        self._step_count += 1
        logger.debug(f"BombermanEnv.step: action={action}, session_id={self.session_id}, step={self._step_count}")
        observation, reward, terminated, truncated, info = self.grpc_client.step(
            action=action,
            session_id=self.session_id,
        )
        if observation is None:
            logger.warning("BombermanEnv.step: received None observation, using zeros")
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)
        self._last_obs = observation
        if terminated or truncated:
            logger.info(
                f"BombermanEnv episode ended: session_id={self.session_id}, "
                f"steps={self._step_count}, reward={reward}, "
                f"terminated={terminated}, truncated={truncated}"
            )
        return observation, float(reward), bool(terminated), bool(truncated), info or {}

    def render(
        self,
        *,
        mode: str = "human",
    ) -> None:
        logger.info("render called", extra={"mode": mode})
        return None

    def close(self) -> None:
        logger.info("close called")

