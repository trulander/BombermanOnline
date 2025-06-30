import logging
from typing import Optional, Tuple

import numpy as np
from stable_baselines3.common.base_class import BaseAlgorithm

from app.agents.base_agent import BaseAgent

logger = logging.getLogger(__name__)


class EnemyAIAgent(BaseAgent):
    """AI agent for controlling enemy units."""

    def __init__(self, model: Optional[BaseAlgorithm] = None):
        super().__init__(model=model)
        logger.info("EnemyAIAgent initialized.")

    def predict(self, observation: np.ndarray, state: Optional[np.ndarray] = None, episode_start: Optional[bool] = None) -> Tuple[int, Optional[np.ndarray]]:
        """Predicts the next action for the enemy unit."""
        if self._model is None:
            logger.warning("No model loaded for EnemyAIAgent. Returning a random action.")
            # Return a random action if no model is loaded
            return np.random.randint(0, 8), None  # Assuming 8 possible actions (0-7)

        try:
            action, next_state = self.model.predict(observation, state=state, episode_start=episode_start)
            if isinstance(action, np.ndarray):
                action = int(action.item()) # Convert numpy int to Python int
            logger.debug(f"EnemyAIAgent predicted action: {action}")
            return action, next_state
        except Exception as e:
            logger.error(f"Error during EnemyAIAgent prediction: {e}", exc_info=True)
            # Fallback to a random action on error
            return np.random.randint(0, 8), None 