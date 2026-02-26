import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from app.fastapi_dependencies import get_training_player_service, get_training_enemy_service
from app.models.training import StartTraining


if TYPE_CHECKING:
    from app.services.trainer_player_service import TrainingPlayerService
    from app.services.trainer_enemy_service import TrainingEnemyService


logger = logging.getLogger(__name__)


training_router = APIRouter(prefix="/training", tags=["training"])


@training_router.post(path="/start_player_training")
def start_player_training(
    payload: StartTraining = Depends(StartTraining),
    training_player_service: "TrainingPlayerService" = Depends(get_training_player_service)
) -> bool:
    logger.info("rest start_training called")
    try:
        training_player_service.start_training(
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
            count_cpu=payload.count_cpu
        )
        logger.info("StartTraining completed successfully")
    except Exception as e:
        logger.error(f"StartTraining failed: {e}", exc_info=True)
        return False
    return True

@training_router.post(path="/start_enemy_training")
def start_enemy_training(
    payload: StartTraining = Depends(StartTraining),
    training_enemy_service: "TrainingEnemyService" = Depends(get_training_enemy_service)
) -> bool:
    logger.info("rest start_training called")
    try:
        training_enemy_service.start_training(
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
            count_cpu=payload.count_cpu
        )
        logger.info("StartTraining completed successfully")
    except Exception as e:
        logger.error(f"StartTraining failed: {e}", exc_info=True)
        return False
    return True

