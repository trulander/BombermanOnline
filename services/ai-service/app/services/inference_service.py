import logging
from functools import lru_cache, cache
from threading import Lock
from typing import Any

import numpy as np
from sb3_contrib import RecurrentPPO

from app.config import settings

logger = logging.getLogger(__name__)


class InferenceService:

    def __init__(self) -> None:
        self.model_path = settings.MODELS_PATH
        logger.info(f"InferenceService initialized, model_path={self.model_path}")
        self._storage: dict = {}
        self._model_lock: Lock = Lock()


    def load_model(
        self,
        model_name: str
    ) -> RecurrentPPO | None:

        model = self._storage.get(model_name)
        if model is None:
            with self._model_lock:
                model = self._storage.get(model_name)
                if model is None:
                    model_file = self.model_path / model_name / f"{model_name}.zip"
                    # model_file = self.model_path / model_name / "best_model.zip"
                    logger.info(f"Loading model from {model_file}")
                    if not model_file.exists():
                        logger.warning(f"Model file not found: {model_file}")
                        return None
                    try:
                        model = RecurrentPPO.load(
                            path=model_file,
                            device="cpu",
                        )
                        self._storage[model_name] = model
                        logger.info(f"Model loaded successfully from {model_file}")
                        return model
                    except Exception as e:
                        logger.error(f"Failed to load model from {model_file}: {e}", exc_info=True)
                        return None
        return model

    @lru_cache
    def _get_state(self, session_id: str) -> dict[str, Any]:
        return {
            session_id: {},
            "episode_start" : True
        }

    def infer_action(
        self,
        observation: dict[str, np.ndarray],
        entity_id: str,
        session_id: str,
        model_name: str
    ) -> int:
        """
        Выполняет инференс действия для указанной сущности в сессии.
        
        Args:
            observation: Наблюдение (состояние игры) для модели
            entity_id: Идентификатор сущности (игрока)
            session_id: Идентификатор сессии игры
            
        Returns:
            Действие (int) для выполнения
            
        Raises:
            RuntimeError: Если модель не загружена
        """
        model = self.load_model(model_name=model_name)
        if model is None:
            logger.error("infer_action called but model is not loaded")
            raise RuntimeError("model is not loaded")
        
        # Получаем состояние LSTM для конкретной сущности в сессии
        session = self._get_state(session_id=session_id)
        lstm_state = session.get(entity_id)
        episode_start: bool = session.get("episode_start")

        # Выполняем предсказание действия
        action, new_lstm_state = model.predict(
            observation=observation,
            state=lstm_state,
            episode_start=np.array([episode_start]),
            deterministic=False,
        )
        
        # Обновляем состояние LSTM для данной сущности в сессии
        session[entity_id] = new_lstm_state
        session["episode_start"] = False

        if isinstance(action, np.ndarray):
            return int(action.item())
        return int(action)
