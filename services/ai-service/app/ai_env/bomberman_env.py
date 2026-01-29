import numpy as np
import gymnasium as gym
from gymnasium import spaces

from app.services.grpc_client import GameServiceGRPCClient


class BombermanEnv(gym.Env[np.ndarray, int]):
    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
        obs_shape: tuple[int, ...] = (1,),
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

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[np.ndarray, dict]:
        super().reset(seed=seed)
        observation, info, session_id = self.grpc_client.reset(options=options)
        if observation is None:
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)
        self.session_id = session_id
        self._last_obs = observation
        return observation, info or {}

    def step(
        self,
        action: int,
    ) -> tuple[np.ndarray, float, bool, bool, dict]:
        observation, reward, terminated, truncated, info = self.grpc_client.step(
            action=action,
            session_id=self.session_id,
        )
        if observation is None:
            observation = np.zeros(self.observation_space.shape, dtype=np.float32)
        self._last_obs = observation
        return observation, float(reward), bool(terminated), bool(truncated), info or {}

