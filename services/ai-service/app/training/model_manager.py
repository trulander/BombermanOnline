import logging
from pathlib import Path
from typing import Optional, Type, TypeVar

from stable_baselines3.common.base_class import BaseAlgorithm
from stable_baselines3 import PPO, A2C, DQN # Import common algorithms

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseAlgorithm)

class ModelManager:
    """Manages saving and loading of Stable Baselines3 AI models."""

    def __init__(self, models_base_path: Path = settings.MODELS_PATH):
        self.models_base_path = models_base_path
        self.models_base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"ModelManager initialized. Models base path: {self.models_base_path}")

    def _get_model_dir(self, game_mode: str) -> Path:
        """Returns the directory for a specific game mode's models."""
        return self.models_base_path / game_mode

    def get_model_path(self, game_mode: str, iteration: int) -> Path:
        """Returns the full path for a specific model iteration."""
        model_dir = self._get_model_dir(game_mode)
        return model_dir / f"model_{iteration}.zip"

    def save_model(self, model: BaseAlgorithm, game_mode: str, iteration: int) -> None:
        """Saves an SB3 model to the specified path."""
        model_dir = self._get_model_dir(game_mode)
        model_dir.mkdir(parents=True, exist_ok=True)
        model_path = self.get_model_path(game_mode, iteration)
        try:
            model.save(model_path)
            logger.info(f"Model for {game_mode} at iteration {iteration} saved to {model_path}")
        except Exception as e:
            logger.error(f"Failed to save model for {game_mode} at iteration {iteration}: {e}", exc_info=True)

    def load_model(self, game_mode: str, iteration: Optional[int] = None, algorithm_class: Type[T] = PPO) -> Optional[T]:
        """Loads an SB3 model. If iteration is None, loads the latest model."""
        model_dir = self._get_model_dir(game_mode)
        if not model_dir.exists():
            logger.info(f"No models found for game mode {game_mode} at path {model_dir}")
            return None

        if iteration is None:
            # Find the latest iteration
            latest_iteration = -1
            latest_model_path: Optional[Path] = None
            for file_path in model_dir.glob("model_*.zip"):
                try:
                    current_iteration = int(file_path.stem.split("_")[1])
                    if current_iteration > latest_iteration:
                        latest_iteration = current_iteration
                        latest_model_path = file_path
                except (IndexError, ValueError):
                    logger.warning(f"Skipping malformed model file name: {file_path.name}")
                    continue
            
            if latest_model_path:
                model_path = latest_model_path
                logger.info(f"Loading latest model for {game_mode}: {latest_model_path}")
            else:
                logger.info(f"No valid models found for {game_mode} in {model_dir}")
                return None
        else:
            model_path = self.get_model_path(game_mode, iteration)
            logger.info(f"Attempting to load model for {game_mode} at iteration {iteration} from {model_path}")

        if not model_path.exists():
            logger.warning(f"Model file not found: {model_path}")
            return None

        try:
            # Specify the algorithm class when loading to ensure correct type
            model = algorithm_class.load(model_path)
            logger.info(f"Model {model_path.name} loaded successfully.")
            return model
        except Exception as e:
            logger.error(f"Failed to load model from {model_path}: {e}", exc_info=True)
            return None 