from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from app.config import settings


class InferenceService:
    def __init__(
        self,
        model_path: Path | None = None,
    ) -> None:
        self.model_path = model_path or settings.MODELS_PATH
        self.model: PPO | None = None

    def load_model(
        self,
        model_name: str = "bomberman_ai.zip",
    ) -> bool:
        model_file = self.model_path / model_name
        if not model_file.exists():
            return False
        self.model = PPO.load(
            path=model_file,
            device="cpu",
        )
        return True

    def infer_action(
        self,
        observation: np.ndarray,
    ) -> int:
        if self.model is None:
            raise RuntimeError("model is not loaded")
        action, _ = self.model.predict(
            observation=observation,
            deterministic=True,
        )
        if isinstance(action, np.ndarray):
            return int(action.item())
        return int(action)

