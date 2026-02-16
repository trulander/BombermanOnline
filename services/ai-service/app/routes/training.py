import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.dependencies import get_training_service
from app.models.training import StartTraining

if TYPE_CHECKING:
    from app.training.trainer import TrainingService


logger = logging.getLogger(__name__)


training_router = APIRouter(prefix="/training", tags=["training"])


@training_router.post(path="/run")
def start_training(
    payload: StartTraining = Depends(StartTraining),
    training_service: "TrainingService" = Depends(get_training_service)
) -> bool:
    logger.info("rest start_training called")
    try:
        training_service.start_training(
            total_timesteps=payload.total_timesteps or 100,
            log_name=payload.log_name or "bomberman_ai",
            enable_render=payload.enable_render or False,
            render_freq=payload.render_freq or 500,
            model_name=payload.model_name,
            enable_checkpointing=payload.enable_checkpointing,
            checkpoint_freq=payload.checkpoint_freq,
            enable_evaluation=payload.enable_evaluation,
            eval_freq=payload.eval_freq,
            n_eval_episodes=payload.n_eval_episodes,
            max_no_improvement_evals=payload.max_no_improvement_evals,
            min_evals=payload.min_evals,
        )
        logger.info("StartTraining completed successfully")
    except Exception as e:
        logger.error(f"StartTraining failed: {e}", exc_info=True)
        return False
    return True
