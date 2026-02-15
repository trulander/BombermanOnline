from pydantic import BaseModel


class StartTraining(BaseModel):
    total_timesteps: int | None = None
    log_name: str | None = None
    enable_render: bool | None = None
    render_freq: int | None = None
    model_name: str | None = None