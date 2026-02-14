import logging

import numpy as np
from stable_baselines3.common.callbacks import BaseCallback
from stable_baselines3.common.logger import Image

logger = logging.getLogger(__name__)


class TensorBoardRenderCallback(BaseCallback):
    def __init__(
        self,
        render_freq: int = 500,
        verbose: int = 0,
    ) -> None:
        super().__init__(verbose=verbose)
        self._render_freq: int = render_freq

    def _on_step(self) -> bool:
        if self.n_calls % self._render_freq != 0:
            return True

        try:
            renders: list = self.training_env.env_method("render")
            frame: np.ndarray | None = renders[0] if renders else None
        except Exception as exc:
            logger.warning(f"render callback failed to get frame: {exc}")
            return True

        if frame is None:
            return True

        self.logger.record(
            key="render/game_view",
            value=Image(image=frame, dataformats="HWC"),
            exclude=("stdout",),
        )
        return True

