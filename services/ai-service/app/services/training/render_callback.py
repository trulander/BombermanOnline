import logging

import numpy as np
from torch.utils.tensorboard import SummaryWriter
from stable_baselines3.common.callbacks import BaseCallback

logger = logging.getLogger(__name__)


class TensorBoardRenderCallback(BaseCallback):
    def __init__(
        self,
        render_freq: int = 500,
        verbose: int = 0,
    ) -> None:
        super().__init__(verbose=verbose)
        self._render_freq: int = render_freq
        self._sw: SummaryWriter | None = None

    def _on_training_start(self) -> None:
        log_dir: str = self.logger.dir
        self._sw = SummaryWriter(log_dir=log_dir)

    def _on_step(self) -> bool:
        if self.n_calls % self._render_freq != 0:
            return True
        if self._sw is None:
            return True

        try:
            renders: list = self.training_env.env_method("render")
            frame: np.ndarray | None = renders[0] if renders else None
        except Exception as exc:
            logger.warning(f"render callback failed to get frame: {exc}")
            return True

        if frame is None:
            return True

        self._sw.add_image(
            tag="render/game_view",
            img_tensor=frame,
            global_step=self.num_timesteps,
            dataformats="HWC",
        )
        self._sw.flush()
        return True

    def _on_training_end(self) -> None:
        if self._sw is not None:
            self._sw.close()
            self._sw = None
