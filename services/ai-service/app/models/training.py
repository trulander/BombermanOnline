from pydantic import BaseModel


class StartTraining(BaseModel):
    total_timesteps: int = 1000
    log_name: str | None = None
    model_name: str | None = None
    enable_render: bool = False
    render_freq: int = 1000
    enable_checkpointing: bool = True
    checkpoint_freq: int = 25000
    enable_evaluation: bool = True
    eval_freq: int = 5000
    n_eval_episodes: int = 3
    max_no_improvement_evals: int = 15
    min_evals: int = 15
    count_cpu: int = 1