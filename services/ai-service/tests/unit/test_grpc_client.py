import numpy as np

from app.services.grpc_client import GameServiceGRPCClient
from app.shared.proto import bomberman_ai_pb2


class FakeStub:
    def Step(self, request: bomberman_ai_pb2.TrainingStepRequest) -> bomberman_ai_pb2.TrainingStepResponse:
        return bomberman_ai_pb2.TrainingStepResponse(
            observation=bomberman_ai_pb2.Observation(values=[0.1, 0.2, 0.3]),
            reward=1.5,
            terminated=False,
            truncated=False,
            info_json='{"ok": true}',
        )

    def Reset(self, request: bomberman_ai_pb2.TrainingResetRequest) -> bomberman_ai_pb2.TrainingResetResponse:
        return bomberman_ai_pb2.TrainingResetResponse(
            session_id="s-1",
            observation=bomberman_ai_pb2.Observation(values=[0.4, 0.5]),
            info_json='{"seed": 1}',
        )


def test_reset_returns_observation_and_info(monkeypatch) -> None:
    client = GameServiceGRPCClient()
    monkeypatch.setattr("app.services.grpc_client.PROTO_AVAILABLE", True)
    client.stub = FakeStub()

    observation, info, session_id = client.reset(options={"map_width": 15})

    assert isinstance(observation, np.ndarray)
    np.testing.assert_allclose(observation, np.array([0.4, 0.5], dtype=np.float32))
    assert info["seed"] == 1
    assert session_id == "s-1"


def test_step_returns_values(monkeypatch) -> None:
    client = GameServiceGRPCClient()
    monkeypatch.setattr("app.services.grpc_client.PROTO_AVAILABLE", True)
    client.stub = FakeStub()

    observation, reward, terminated, truncated, info = client.step(action=1, session_id="s-1")

    np.testing.assert_allclose(observation, np.array([0.1, 0.2, 0.3], dtype=np.float32))
    assert reward == 1.5
    assert terminated is False
    assert truncated is False
    assert info["ok"] is True

