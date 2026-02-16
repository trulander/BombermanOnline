import logging

import numpy as np
import gymnasium as gym
from gymnasium import spaces
from PIL import Image, ImageDraw

from app.services.grpc_client import GameServiceGRPCClient

logger = logging.getLogger(__name__)

GRID_CHANNELS: int = 5
WINDOW_SIZE: int = 7
STATS_SIZE: int = 7

RENDER_SCALE: int = 32

COLOR_BACKGROUND: tuple[int, int, int] = (25, 25, 25)
COLOR_SOLID: tuple[int, int, int] = (120, 120, 120)
COLOR_BREAKABLE: tuple[int, int, int] = (160, 82, 45)
COLOR_EXIT: tuple[int, int, int] = (0, 200, 80)
COLOR_PLAYER: tuple[int, int, int] = (0, 120, 255)
COLOR_ENEMY: tuple[int, int, int] = (220, 30, 30)
COLOR_WEAPON: tuple[int, int, int] = (255, 220, 0)
COLOR_POWERUP: tuple[int, int, int] = (200, 0, 255)
COLOR_GRID_LINE: tuple[int, int, int] = (50, 50, 50)

STATS_LABELS: list[str] = [
    # "rel_x",
    # "rel_y",
    "lives",
    "enemies",
    "bombs",
    "range",
    "invuln",
    "speed",
    "time",
]


class BombermanEnv(gym.Env[dict[str, np.ndarray], int]):
    metadata: dict = {"render_modes": ["rgb_array"]}

    def __init__(
        self,
        grpc_client: GameServiceGRPCClient,
        grid_shape: tuple[int, ...] = (GRID_CHANNELS, WINDOW_SIZE, WINDOW_SIZE),
        stats_size: int = STATS_SIZE,
        action_count: int = 6,
        render_mode: str | None = None,
    ) -> None:
        self.grpc_client = grpc_client
        self.render_mode = render_mode
        self.action_space = spaces.Discrete(n=action_count)
        self.observation_space = spaces.Dict(
            {
                "grid": spaces.Box(
                    low=0.0,
                    high=1.0,
                    shape=grid_shape,
                    dtype=np.float32,
                ),
                "stats": spaces.Box(
                    low=0.0,
                    high=1.0,
                    shape=(stats_size,),
                    dtype=np.float32,
                ),
            }
        )
        self._grid_shape: tuple[int, ...] = grid_shape
        self._stats_size: int = stats_size
        self.session_id: str | None = None
        self._last_obs: dict[str, np.ndarray] = self._empty_obs()
        self._step_count: int = 0
        logger.info(
            f"BombermanEnv initialized: grid_shape={grid_shape}, "
            f"stats_size={stats_size}, action_count={action_count}, "
            f"render_mode={render_mode}"
        )

    def _empty_obs(self) -> dict[str, np.ndarray]:
        return {
            "grid": np.zeros(self._grid_shape, dtype=np.float32),
            "stats": np.zeros(self._stats_size, dtype=np.float32),
        }

    def reset(
        self,
        *,
        seed: int | None = None,
        options: dict[str, object] | None = None,
    ) -> tuple[dict[str, np.ndarray], dict]:
        super().reset(seed=seed)
        logger.info(f"BombermanEnv.reset called: seed={seed}, options={options}")
        self._step_count = 0
        observation, info, session_id = self.grpc_client.reset(options=options)
        if observation is None:
            logger.warning("BombermanEnv.reset: received None observation, using zeros")
            observation = self._empty_obs()
        self.session_id = session_id
        self._last_obs = observation
        logger.info(f"BombermanEnv.reset completed: session_id={session_id}")
        return observation, info or {}

    def step(
        self,
        action: int,
    ) -> tuple[dict[str, np.ndarray], float, bool, bool, dict]:
        self._step_count += 1
        logger.debug(f"BombermanEnv.step: action={action}, session_id={self.session_id}, step={self._step_count}")
        observation, reward, terminated, truncated, info = self.grpc_client.step(
            action=action,
            session_id=self.session_id,
        )
        if observation is None:
            logger.warning("BombermanEnv.step: received None observation, using zeros")
            observation = self._empty_obs()
        self._last_obs = observation
        if terminated or truncated:
            logger.info(
                f"BombermanEnv episode ended: session_id={self.session_id}, "
                f"steps={self._step_count}, reward={reward}, "
                f"terminated={terminated}, truncated={truncated}"
            )
        return observation, float(reward), bool(terminated), bool(truncated), info or {}

    def render(self) -> np.ndarray | None:
        if self.render_mode != "rgb_array":
            return None

        grid: np.ndarray = self._last_obs["grid"]
        stats: np.ndarray = self._last_obs.get("stats", np.zeros(self._stats_size, dtype=np.float32))

        _, h, w = grid.shape
        img: np.ndarray = np.full((h, w, 3), fill_value=COLOR_BACKGROUND, dtype=np.uint8)

        terrain: np.ndarray = grid[0]
        img[terrain == 1.0] = COLOR_SOLID
        img[(terrain > 0.4) & (terrain < 0.6)] = COLOR_BREAKABLE
        img[(terrain > 0.2) & (terrain < 0.3)] = COLOR_EXIT

        img[grid[4] == 1.0] = COLOR_POWERUP
        img[grid[3] == 1.0] = COLOR_WEAPON
        img[grid[2] == 1.0] = COLOR_ENEMY
        img[grid[1] == 1.0] = COLOR_PLAYER

        scaled: np.ndarray = np.repeat(np.repeat(img, RENDER_SCALE, axis=0), RENDER_SCALE, axis=1)

        for row in range(1, h):
            scaled[row * RENDER_SCALE, :] = COLOR_GRID_LINE
        for col in range(1, w):
            scaled[:, col * RENDER_SCALE] = COLOR_GRID_LINE

        pil_img: Image.Image = Image.fromarray(scaled)
        draw: ImageDraw.ImageDraw = ImageDraw.Draw(im=pil_img)

        y_offset: int = 4
        for i, label in enumerate(STATS_LABELS):
            if i < len(stats):
                draw.text(xy=(4, y_offset), text=f"{label}: {stats[i]:.2f}", fill=(255, 255, 255))
                y_offset += 16

        return np.array(pil_img)

    def close(self) -> None:
        logger.info("close called")
