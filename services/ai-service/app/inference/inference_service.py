import logging

import numpy as np
from stable_baselines3 import PPO

from app.config import settings

logger = logging.getLogger(__name__)


class InferenceService:
    def __init__(self) -> None:
        self.model_path = settings.MODELS_PATH
        self.model: PPO | None = None
        logger.info(f"InferenceService initialized, model_path={self.model_path}")

    def load_model(
        self,
        model_name: str = "bomberman_ai.zip",
    ) -> bool:
        model_file = self.model_path / model_name
        logger.info(f"Loading model from {model_file}")
        if not model_file.exists():
            logger.warning(f"Model file not found: {model_file}")
            return False
        try:
            self.model = PPO.load(
                path=model_file,
                device="cpu",
            )
            logger.info(f"Model loaded successfully from {model_file}")
        except Exception as e:
            logger.error(f"Failed to load model from {model_file}: {e}", exc_info=True)
            return False
        return True

    def infer_action(
        self,
        observation: np.ndarray,
    ) -> int:
        if self.model is None:
            logger.error("infer_action called but model is not loaded")
            raise RuntimeError("model is not loaded")
        action, _ = self.model.predict(
            observation=observation,
            deterministic=True,
        )
        if isinstance(action, np.ndarray):
            return int(action.item())
        return int(action)

