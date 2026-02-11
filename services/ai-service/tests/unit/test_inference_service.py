from pathlib import Path

import numpy as np

from app.inference.inference_service import InferenceService


class FakeModel:
    def predict(self, *, observation: np.ndarray, deterministic: bool) -> tuple[np.ndarray, None]:
        return np.array([2], dtype=np.int64), None


class FakePPO:
    @staticmethod
    def load(*, path: Path, device: str) -> FakeModel:
        return FakeModel()


def test_load_model_uses_ppo(monkeypatch, tmp_path: Path) -> None:
    model_path = tmp_path / "bomberman_ai.zip"
    model_path.write_bytes(b"test")
    service = InferenceService(model_path=tmp_path)
    monkeypatch.setattr("app.inference.inference_service.PPO", FakePPO)

    loaded = service.load_model(model_name="bomberman_ai.zip")

    assert loaded is True
    assert isinstance(service.model, FakeModel)


def test_infer_action_returns_int() -> None:
    service = InferenceService(model_path=Path("."))
    service.model = FakeModel()

    action = service.infer_action(observation=np.array([0.1], dtype=np.float32))

    assert action == 2

