from pydantic import BaseModel


class StartTraining(BaseModel):
    total_timesteps: int | None = None
    log_name: str | None = None
    enable_render: bool | None = None
    render_freq: int | None = None
    model_name: str | None = None
    enable_checkpointing: bool | None = None
    checkpoint_freq: int | None = None
    enable_evaluation: bool | None = None
    eval_freq: int | None = None
    n_eval_episodes: int | None = None
    max_no_improvement_evals: int | None = None
    min_evals: int | None = None