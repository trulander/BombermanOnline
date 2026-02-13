from pydantic import BaseModel


class StartTraining(BaseModel):
    total_timesteps: int | None
    log_name: str | None