import numpy as np

from app.ai_env.bomberman_env import BombermanEnv


class FakeClient:
    def __init__(self) -> None:
        self.reset_called = False
        self.step_called = False

    def reset(self, options: dict[str, object] | None = None) -> tuple[np.ndarray, dict, str]:
        self.reset_called = True
        return np.ones((231,), dtype=np.float32), {"ok": True}, "session-1"

    def step(self, action: int, session_id: str | None) -> tuple[np.ndarray, float, bool, bool, dict]:
        self.step_called = True
        return np.zeros((231,), dtype=np.float32), 0.5, False, False, {"step": True}


def test_env_reset_and_step() -> None:
    client = FakeClient()
    env = BombermanEnv(grpc_client=client)

    observation, info = env.reset()
    next_obs, reward, terminated, truncated, step_info = env.step(action=1)

    assert client.reset_called is True
    assert client.step_called is True
    assert observation.shape == (231,)
    assert info["ok"] is True
    assert next_obs.shape == (231,)
    assert reward == 0.5
    assert terminated is False
    assert truncated is False
    assert step_info["step"] is True

