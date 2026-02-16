import logging
from typing import Any

import numpy as np
from sb3_contrib import RecurrentPPO

from app.config import settings

logger = logging.getLogger(__name__)


class InferenceService:
    def __init__(self) -> None:
        self.model_path = settings.MODELS_PATH
        self.model: RecurrentPPO | None = None
        self._lstm_states: dict[str, Any] = {}
        self._episode_starts: dict[str, bool] = {}
        logger.info(f"InferenceService initialized, model_path={self.model_path}")

    def load_model(
        self,
        model_name: str = "20000.zip",
    ) -> bool:
        model_file = self.model_path / model_name
        logger.info(f"Loading model from {model_file}")
        if not model_file.exists():
            logger.warning(f"Model file not found: {model_file}")
            return False
        try:
            self.model = RecurrentPPO.load(
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
        observation: dict[str, np.ndarray],
        entity_id: str,
        session_id: str
    ) -> int:
        if self.model is None:
            logger.error("infer_action called but model is not loaded")
            raise RuntimeError("model is not loaded")

        lstm_state = self._lstm_states.get(entity_id)
        episode_start: bool = self._episode_starts.pop(entity_id, lstm_state is None)

        action, new_lstm_state = self.model.predict(
            observation=observation,
            state=lstm_state,
            episode_start=np.array([episode_start]),
            deterministic=True,
        )
        self._lstm_states[entity_id] = new_lstm_state

        if isinstance(action, np.ndarray):
            return int(action.item())
        return int(action)

    def reset_entity(self, entity_id: str) -> None:
        self._episode_starts[entity_id] = True

    def remove_entity(self, entity_id: str) -> None:
        self._lstm_states.pop(entity_id, None)
        self._episode_starts.pop(entity_id, None)
