import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Tuple

import numpy as np
from stable_baselines3.common.base_class import BaseAlgorithm

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents."""

    def __init__(self, model: Optional[BaseAlgorithm] = None):
        self._model = model
        logger.info(f"BaseAgent initialized. Model loaded: {self._model is not None}")

    @property
    def model(self) -> BaseAlgorithm:
        if self._model is None:
            raise ValueError("AI model not loaded for this agent.")
        return self._model

    @model.setter
    def model(self, new_model: BaseAlgorithm) -> None:
        self._model = new_model
        logger.info("AI model updated for BaseAgent.")

    @abstractmethod
    def predict(self, observation: np.ndarray, state: Optional[np.ndarray] = None, episode_start: Optional[bool] = None) -> Tuple[int, Optional[np.ndarray]]:
        """Predicts the next action based on the observation."""
        pass

    def load_model_from_path(self, path: str) -> None:
        """Loads a Stable Baselines3 model from the given path."""
        try:
            self._model = BaseAlgorithm.load(path)
            logger.info(f"Model loaded successfully from {path}")
        except Exception as e:
            logger.error(f"Failed to load model from {path}: {e}", exc_info=True)
            self._model = None # Ensure model is None if loading fails 